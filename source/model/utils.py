import os
import uuid
import torch
import random
import numpy as np
import torch.nn as nn
import torch.optim as optim
from source import model_settings, log


def set_seed(seed=42) -> None:
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    np.random.seed(seed)
    random.seed(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False

def model_tool(model:nn.Module):

    criterion = nn.MSELoss()
    optimizer = optim.Adam(
        model.parameters(),
        lr=float(model_settings["training"]["learning_rate"]),
        weight_decay=float(model_settings["training"].get("weight_decay", 1e-5))  # 添加 L2 正则
    )

    scheduler = optim.lr_scheduler.ReduceLROnPlateau(
        optimizer,
        mode='min',
        factor=0.5,
        patience=3,
        min_lr=1e-7
    )

    return criterion, optimizer, scheduler

def generate_random_version_key() -> str:
    """生成16位随机密钥（用于训练脚本）"""
    return str(uuid.uuid4()).replace('-', '')[:32]

def update_model_version(version_path) -> None:

    version_key = generate_random_version_key()
    with open(version_path, 'w') as f:
        f.write(version_key)
    log.info(f"模型更新：模型密钥变更{version_key[:6]}")