# 电厂变负荷调节优化系统

## 项目简介

本项目是一个面向电厂的变负荷调节优化系统，旨在通过机器学习和优化算法，实现电厂负荷的精准预测和高效调节，提高电厂运行的经济性和稳定性。

## 核心功能

- **负荷预测**：基于人工神经网络(ANN)模型，预测电厂实时负荷
- **负荷优化**：使用贝叶斯优化算法，寻找最优控制参数组合
- **实时数据处理**：与Redis和TDengine数据库集成，获取和处理实时运行数据
- **Web API接口**：提供RESTful API，支持外部系统调用
- **任务调度**：通过APScheduler实现定时任务管理

## 技术栈

- **后端框架**：Python, FastAPI, uvicorn
- **机器学习**：PyTorch, ONNX, scikit-learn
- **优化算法**：Bayesian Optimization
- **数据库**：Redis, TDengine
- **任务调度**：APScheduler
- **配置管理**：PyYAML

## 项目结构

```
fanggang/
├── config/             # 配置文件目录
│   └── config.yaml     # 系统配置
├── models/             # 模型文件目录
│   ├── best_model.onnx # ONNX格式模型
│   ├── best_model.pth  # PyTorch模型
│   ├── scaler.pkl      # 数据标准化器
│   └── training_history.png # 训练历史图
├── source/             # 源代码目录
│   ├── core/           # 核心功能模块
│   ├── database/       # 数据库操作模块
│   ├── errors/         # 错误处理模块
│   ├── model/          # 模型相关模块
│   ├── routers/        # API路由模块
│   ├── scheduler/      # 任务调度模块
│   └── utils/          # 工具函数模块
├── data.csv            # 训练数据
├── main.py             # 主入口文件
├── requirements.txt    # 依赖文件
└── README.md           # 项目说明文档
```

## 系统架构

1. **数据层**：通过Redis和TDengine获取实时运行数据
2. **模型层**：使用ANN神经网络进行负荷预测
3. **优化层**：使用贝叶斯优化算法寻找最优控制参数
4. **服务层**：通过FastAPI提供Web API接口
5. **调度层**：使用APScheduler管理定时任务

## 安装与部署

### 环境要求

- Python 3.12+
- Redis 6.0+
- TDengine 3.0+

### 安装依赖

```bash
pip install -r requirements.txt
```

### 配置文件

修改 `config/config.yaml` 文件，根据实际情况配置以下参数：

- **数据配置**：训练数据路径、输入输出参数
- **模型配置**：模型结构、训练参数
- **优化配置**：优化算法参数、控制参数范围
- **数据库配置**：Redis和TDengine连接信息
- **API配置**：FastAPI服务地址和端口

### 启动服务

```bash
python main.py
```

服务默认运行在 `http://0.0.0.0:8012`，可通过配置文件修改。

## API接口

### 模型预测接口

- **URL**：`/open-api/model/predict`
- **方法**：POST
- **参数**：输入特征向量
- **返回**：预测的负荷值

### 负荷优化接口

- **URL**：`/open-api/model/optimize`
- **方法**：POST
- **参数**：实时运行参数、目标负荷
- **返回**：优化后的控制参数

## 模型训练

### 数据准备

将训练数据保存为 `data.csv` 文件，包含输入特征和目标负荷值。

### 模型训练

系统启动时会自动加载已有模型，如果需要重新训练模型，可以修改代码中的相关参数。

## 系统监控

- **日志文件**：保存在 `logs/` 目录下
- **模型性能**：训练过程和预测结果会生成可视化图表
- **系统状态**：通过API接口可以查询系统运行状态

## 注意事项

1. 确保Redis和TDengine服务正常运行
2. 首次运行时需要准备足够的训练数据
3. 模型训练过程可能需要较长时间，取决于数据量和硬件性能
4. 生产环境中建议使用ONNX格式模型以提高推理速度

## 维护与更新

- **模型更新**：定期使用新数据重新训练模型，提高预测精度
- **参数调整**：根据实际运行情况调整优化算法参数
- **系统监控**：定期检查系统运行状态和日志，确保系统稳定运行

## 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 联系方式

- 项目维护者: Hakutaku23
- 邮箱: [y1486483811@email.swu.edu.cn](mailto:y1486483811@email.swu.edu.cn)

## 致谢

感谢所有为项目做出贡献的开发者和研究人员！

---

*Created By Hakutaku23. PSELAB Chongqing China. All rights reserved.*