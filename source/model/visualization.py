import zhplot
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from source import log
from sklearn.metrics import mean_absolute_error, r2_score, mean_absolute_percentage_error, mean_squared_error


def plot_training_history(history, save_path):
    
    
    plt.figure(figsize=(10, 5))
    plt.plot(history['train_loss'], label='训练损失')
    plt.plot(history['val_loss'], label='验证损失')
    plt.xlabel('轮次')
    plt.ylabel('损失（MSE）')
    plt.title('训练集与测试集损失')
    plt.legend()
    plt.savefig(save_path)
    plt.close()
    
    log.info(f"模型训练历史记录已保存到：{save_path}")

def plot_true_vs_predicted(true_values, predicted_values, title="True vs Predicted Values", save_path="prediction_comparison.png"):
    """
    绘制真实值与预测值的对比散点图，并保存结果
    
    参数:
    true_values: 真实值数组 (numpy array)
    predicted_values: 预测值数组 (numpy array)
    title: 图表标题
    save_path: 保存路径
    """
    plt.figure(figsize=(12, 10))
    
    # 创建散点图
    sns.scatterplot(
        x=true_values.flatten(),
        y=predicted_values.flatten(),
        alpha=0.6,
        color='blue',
        edgecolor='w',
        linewidth=0.5
    )
    
    # 添加对角线参考线
    min_val = min(np.min(true_values), np.min(predicted_values))
    max_val = max(np.max(true_values), np.max(predicted_values))
    plt.plot([min_val, max_val], [min_val, max_val], 'r--', lw=2, label='最佳预测值')
    
    # 添加均值参考线
    mean_true = np.mean(true_values)
    plt.axhline(y=mean_true, color='g', linestyle='-', alpha=0.5, label=f'真实值均值: {mean_true:.2f}')
    plt.axvline(x=mean_true, color='g', linestyle='-', alpha=0.5, label=f'真实值均值: {mean_true:.2f}')
    
    # 添加评估指标
    # mse = np.mean((true_values - predicted_values) ** 2)
    # r2 = 1 - (np.sum((true_values - predicted_values) ** 2) / 
    #           np.sum((true_values - np.mean(true_values)) ** 2))
    mse = mean_squared_error(true_values, predicted_values)
    r2 = r2_score(true_values, predicted_values)
    mae = mean_absolute_error(true_values, predicted_values)
    mape = mean_absolute_percentage_error(true_values, predicted_values)
    
    plt.text(0.05, 0.95, f'MSE: {mse:.4f}\nR²: {r2:.4f}\nMAE:{mae:.4f}\nMAPE:{mape:.4f}', 
             transform=plt.gca().transAxes, fontsize=12,
             verticalalignment='top', bbox=dict(boxstyle="round", 
                                              facecolor="white", alpha=0.8))
    
    # 添加标签和标题
    plt.xlabel('真实值', fontsize=14, labelpad=10)
    plt.ylabel('预测值', fontsize=14, labelpad=10)
    plt.title(title, fontsize=16, pad=20)
    plt.legend(fontsize=12)
    
    # 设置坐标轴范围
    plt.xlim(min_val * 0.95, max_val * 1.05)
    plt.ylim(min_val * 0.95, max_val * 1.05)
    
    # 添加网格线
    plt.grid(True, linestyle='--', alpha=0.7)
    
    # 优化布局
    plt.tight_layout()
    
    # 保存图表
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    log.info(f"预测值可视化图已保存到'{save_path}'")
    log.info(f"模型验证结果: MSE={mse:.4f}, R²={r2:.4f}")
    return {
        "MSE": mse,
        "MAE": mae,
        "MAPE": mape,
        "R2": r2
    }