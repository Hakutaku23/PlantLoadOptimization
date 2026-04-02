import os
import torch
import joblib
import onnxruntime
import numpy as np
import torch.nn as nn
from pathlib import Path
from source import log, model_settings


class ANNNetwork(nn.Module):
    def __init__(self, input_dim, output_dim, config):
        super(ANNNetwork, self).__init__()
        layers = []
        
        # 第一层
        linear1 = nn.Linear(input_dim, config['hidden_layers'][0])
        nn.init.kaiming_normal_(linear1.weight, nonlinearity='relu')
        nn.init.zeros_(linear1.bias)
        layers.append(linear1)
        layers.append(nn.ReLU())
        
        # 中间层
        for i in range(len(config['hidden_layers']) - 1):
            linear = nn.Linear(config['hidden_layers'][i], config['hidden_layers'][i+1])
            nn.init.kaiming_normal_(linear.weight, nonlinearity='relu')
            nn.init.zeros_(linear.bias)
            layers.append(linear)
            layers.append(nn.ReLU())
            # layers.append(nn.Dropout(config.get('dropout', 0.3)))
        
        out_layer = nn.Linear(config['hidden_layers'][-1], output_dim)
        nn.init.xavier_normal_(out_layer.weight)  # 或 normal_
        nn.init.zeros_(out_layer.bias)
        layers.append(out_layer)
        
        self.model = nn.Sequential(*layers)

    def forward(self, x):
        return self.model(x)


class Module:
    def __init__(self, path: Path, model_type:str):

        if model_type not in ["torch", "onnx"]:
            raise ValueError(model_type)
        self.model_path = Path(os.path.join(path, "best_model.pth")) if model_type == "torch" else Path(os.path.join(path, "best_model.onnx"))
        self.scaler_path = Path(os.path.join(path, "scaler.pkl"))
        self.version_file = Path(os.path.join(path, "model_version.txt"))
        self.model_type = None
        self.model_version = None  # 保存当前模型的版本密钥
        self.model = self.load_model()

    def load_model(self):
        """加载模型并生成/更新版本密钥"""
        if self.model_path.suffix == ".pth":
            self.model_type = "torch"
            self.model = ANNNetwork(model_settings["input_dim"], model_settings["output_dim"], model_settings)
            save_dict = torch.load(self.model_path)
            self.model.load_state_dict(save_dict['model_state_dict'])
            self.model.eval()
        elif self.model_path.suffix == ".onnx":
            self.model_type = "onnx"
            self.model = onnxruntime.InferenceSession(str(self.model_path))
        
        self.scaler = joblib.load(self.scaler_path)
        # 生成当前模型的版本密钥
        # self.model_version = self._generate_version_key(self.model_path)
        self.model_version = self._read_current_version()
        
        # # 写入版本文件（覆盖写）
        # with open(self.version_file, 'w') as f:
        #     f.write(self.model_version)
        
        log.info(f"✅ 模型加载成功 (版本密钥: {self.model_version[:8]}...)")
        return self.model
    
    def _check_model(self):

        current_version = self._read_current_version()

        if current_version != self.model_version:
            log.info(f"🔄 检测到模型更新 (当前: {current_version[:8]}..., 旧版本: {self.model_version[:8]}...)")
            self.load_model()

    def predict(self, inputs:np.ndarray):
        """推理前检查版本匹配"""
        self._check_model()

        inputs = inputs.reshape(1, -1)
        inputs = self.scaler.transform(inputs).astype(np.float32)
        # 执行推理
        if self.model_type == "torch":
            return self._torch_predict(inputs)
        elif self.model_type == "onnx":
            return self._onnx_predict(inputs)
        
    def predict_obj(self, inputs:np.ndarray) -> float:

        self._check_model()

        inputs = inputs.reshape(1, -1)
        inputs = self.scaler.transform(inputs).astype(np.float32)
        # 执行推理
        if self.model_type == "torch":
            return self._torch_predict(inputs).ravel()[0]
        elif self.model_type == "onnx":
            return self._onnx_predict(inputs).ravel()[0]

    def _read_current_version(self) -> str:
        """读取版本文件中的密钥（安全处理）"""
        if not os.path.exists(self.version_file):
            return "0"
        try:
            with open(self.version_file, 'r') as f:
                return f.readline().strip()
        except Exception as e:
            print(f"⚠️ 读取版本文件失败: {e}")
            return "0"

    def _torch_predict(self, inputs):
        """PyTorch推理实现"""
        # self.model.eval()
        inputs = torch.tensor(inputs, dtype=torch.float32)
        with torch.no_grad():
            return self.model(inputs).cpu().numpy()

    def _onnx_predict(self, inputs):
        """ONNX推理实现"""
        input_name = self.model.get_inputs()[0].name
        return self.model.run(None, {input_name: inputs})[0]