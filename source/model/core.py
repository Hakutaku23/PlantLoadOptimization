import os
import time
import torch
import joblib
import numpy as np
from source.model.model import ANNNetwork
from source.model.utils import set_seed, model_tool, update_model_version
from source.model.dataset import GPUDataset
from source.model.visualization import plot_training_history, plot_true_vs_predicted
from pathlib import Path
from torch.utils.data import DataLoader
from sklearn.preprocessing import RobustScaler
from sklearn.model_selection import train_test_split
from source import log, settings, MODEL_PATH, model_settings


def model_train(x:np.ndarray, y:np.ndarray, x_test:np.ndarray, y_test:np.ndarray, retrain:bool=False):

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    set_seed(settings.settings.get("seed", 42))
    x_train, x_val, y_train, y_val = train_test_split(x, y, test_size=model_settings.get("test_size", 0.2))
    model_path = Path(os.path.join(MODEL_PATH, "best_model.pth"))
    scaler_path = Path(os.path.join(MODEL_PATH, "scaler.pkl"))
    history_path = Path(os.path.join(MODEL_PATH, "training_history.png"))
    model_version = Path(os.path.join(MODEL_PATH, "model_version.txt"))
    val_path = Path(os.path.join(MODEL_PATH, "prediction_comparison.png"))

    if not retrain:
        try:
            save_dict = torch.load(model_path)
            model = ANNNetwork(x_train.shape[1], y_train.shape[1], model_settings)
            model.load_state_dict(save_dict['model_state_dict'])

            if 'optimizer_state_dict' in save_dict:
                optimizer.load_state_dict(save_dict['optimizer_state_dict'])
                log.info("✅ 模型和优化器状态加载成功，从上次训练点继续")
            else:
                log.warning("⚠️ 只有模型状态加载成功，优化器将重新初始化")
            resume = True
        except Exception as e:
            log.error(f"❌️ 增量训练出错：{e}")
            model = ANNNetwork(x_train.shape[1], y_train.shape[1], model_settings)
            criterion, optimizer, scheduler = model_tool(model)
            log.info("🔄 正在初始化新模型")
            resume = False
    else:
        log.info("✅ 正在重新训练模型，模型创建成功")
        model = ANNNetwork(x_train.shape[1], y_train.shape[1], model_settings)
        criterion, optimizer, scheduler = model_tool(model)
        log.info("🔄 正在初始化新模型")
        resume = False

    if resume:
        for param_group in optimizer.param_groups:
            param_group['lr'] *= 0.5  # 学习率减半

    if resume and scaler_path.exists():
        scaler = joblib.load(scaler_path)
        log.info("♻️ 使用已有的scaler进行数据预处理")
    else:
        scaler = RobustScaler()
        scaler = scaler.fit(x_train)
        joblib.dump(scaler, scaler_path)
    
    train_dataset = GPUDataset(x_train, y_train, scaler=scaler)
    val_dataset = GPUDataset(x_val, y_val, scaler=scaler)
    test_dataset = GPUDataset(x_test, y_test, scaler=scaler)
    train_loader = DataLoader(
        train_dataset, 
        batch_size=model_settings["training"]["batch_size"],
        shuffle=True,
        num_workers=4,
        pin_memory=True
    )
    val_loader = DataLoader(
        val_dataset,
        batch_size=model_settings["training"]["batch_size"],
        shuffle=False,
        num_workers=4,
        pin_memory=True
    )
    test_loader = DataLoader(
        test_dataset,
        batch_size=model_settings["training"]["batch_size"],
        shuffle=False,
        num_workers=4,
        pin_memory=True
    )
    min_delta = float(model_settings["training"].get("min_delta", 1e-4))
    log.info(f"模型训练开始，训练集大小：{x_train.shape}，验证集大小：{x_val.shape}")
    start = time.time()
    history, model = _model_train(
        model=model,
        train_loader=train_loader,
        val_loader=val_loader,
        criterion=criterion,
        optimizer=optimizer,
        scheduler=scheduler,
        min_delta=min_delta,
        epochs=model_settings["training"]["epochs"],
        device=device
    )
    log.info(f"模型训练结束，耗时：{(time.time()-start)*1000:.2f}s")
    _model_save(model, optimizer, model_path, model_settings["type"])
    update_model_version(model_version)

    model.eval()  # ✅ 设置模型为评估模式
    log.info("🔍 开始模型测试评估")
    test_predictions = []
    true_values = []
    with torch.no_grad():
        for inputs, labels in test_loader:
            inputs = inputs.to(device)
            labels = labels.to(device)
            outputs = model(inputs)
            test_predictions.append(outputs.cpu().numpy())
            true_values.append(labels.cpu().numpy())
    test_predictions = np.vstack(test_predictions)
    true_values = np.vstack(true_values)
    
    plot_training_history(history, history_path)
    metrics = plot_true_vs_predicted(
        true_values, 
        test_predictions, 
        title="测试集：真实值与预测值对比",
        save_path=val_path
    )

    return metrics

def _model_save(model, optimizer, model_path:Path, model_type:str):
    """新增优化器保存"""
    
    if model_type == "onnx":
        try:
            input_dim = model.model[0].in_features
        except Exception as e:
            raise ValueError("无法自动获取输入维度！请确保模型结构包含第一层线性层（例如：ANNNetwork）") from e
        
        dummy_input = torch.randn(1, input_dim)
        onnx_path = model_path.with_suffix(".onnx")
        torch.onnx.export(
            model,
            dummy_input,
            onnx_path,
            opset_version=11,
            input_names=["input"],
            output_names=["output"],
            dynamic_axes={
                "input": {0: "batch_size"},
                "output": {0: "batch_size"}
            }
        )

    save_dict = {
        'model_state_dict': model.state_dict(),
        'optimizer_state_dict': optimizer.state_dict()
    }
    torch.save(save_dict, model_path)
    
def _model_test(model, model_type, x_test, y_test):
    ...

def _model_train(model, train_loader, val_loader, criterion, optimizer, scheduler=None, 
                epochs=100, patience=10, min_delta=1e-4, device="cpu") -> dict:
    model.train()
    best_val_loss = float('inf')
    counter = 0
    history = {'train_loss': [], 'val_loss': []}
    best_model_state = None
    
    for epoch in range(epochs):
        total_loss = 0
        for inputs, labels in train_loader:
            inputs = inputs.to(device)
            labels = labels.to(device)
            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)  # 梯度裁剪
            optimizer.step()
            total_loss += loss.item()
        
        val_loss = 0
        model.eval()
        with torch.no_grad():
            for inputs, labels in val_loader:
                inputs = inputs.to(device)
                labels = labels.to(device)
                outputs = model(inputs)
                loss = criterion(outputs, labels)
                val_loss += loss.item()
        model.train()
        
        avg_train_loss = total_loss / len(train_loader)
        avg_val_loss = val_loss / len(val_loader)
        
        # 早停 + 保存
        if avg_val_loss < best_val_loss - min_delta:
            best_val_loss = avg_val_loss
            # torch.save(model.state_dict(), 'best_model.pth')
            best_model_state = model.state_dict().copy()
            counter = 0
        else:
            counter += 1
        
        if counter >= patience:
            log.info(f"Early stopping at epoch {epoch+1}")
            break
        
        history['train_loss'].append(avg_train_loss)
        history['val_loss'].append(avg_val_loss)
        
        # 学习率调度
        if scheduler is not None:
            scheduler.step(avg_val_loss)
            current_lr = optimizer.param_groups[0]['lr']
            log.debug(f"Epoch {epoch+1}/{epochs} | Train Loss: {avg_train_loss:.4f} | "
                        f"Val Loss: {avg_val_loss:.4f} | LR: {current_lr:.2e}")
        else:
            log.debug(f"Epoch {epoch+1}/{epochs} | Train Loss: {avg_train_loss:.4f} | Val Loss: {avg_val_loss:.4f}")
    
    if best_model_state is not None:
        model.load_state_dict(best_model_state)
        log.info("✅ 已加载最佳模型状态")

    return history, model

