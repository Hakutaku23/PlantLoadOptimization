import time
import numpy as np
from bayes_opt import BayesianOptimization
from source import log, settings
from source.model.model import Module



class LoadControlSystem:
    def __init__(self, model:Module, config:dict):
        """
        初始化负荷控制系统
        
        :param ann_model_path: ANN模型
        :param config: 负荷优化控制系统配置参数
        """
        self.control_params = config["optimize"]["params"]
        self.bounds_persent = config["optimize"]["bounds_persent"]
        self.size = config["optimize"]["size"]
        self.iters = config["optimize"]["iters"]
        self.model = model
        self.x = settings.x_params

        # 初始化贝叶斯优化器
        # self._init_bayesian_optimizer()
        
        # # 系统状态
        # self.current_load = 0.0
        # self.last_update_time = time.time()
        # self.iteration_count = 0
        # self.max_iterations = 10  # 5分钟 * 60秒 / 30秒 = 10次
        # self.convergence_threshold = 0.5  # 负荷误差阈值 (%)
        
        log.info(f"负荷优化控制系统参数：{len(self.control_params)} 个参数")
        log.info(f"控制参数: {self.control_params}")

    def _objective_function(self, **kwargs):
        """
        贝叶斯优化目标函数
        x: 控制参数向量 (n_params,)
        """
        x = np.array(list(kwargs.values()))
        # 转换为numpy数组
        x = x.reshape(1, -1)
        
        # 预测负荷
        predicted_load = self.model.predict_obj(x)

        error = (predicted_load - self.target_load) ** 2
        return -error

    def _init_bayesian_optimizer(self, realtime_data):
        """初始化贝叶斯优化器"""
        pbounds = {}
        self.bounds = []
        for i, param in enumerate(self.x):
            if param in self.control_params:
                realtime_data[param] = 1e-8 if realtime_data[param] == 0. else realtime_data[param]
                low = realtime_data[param] * (1 - self.bounds_persent)
                high = realtime_data[param] * (1 + self.bounds_persent)
            else:
                low = realtime_data[param] - 1e-8
                high = realtime_data[param] + 1e-8
            pbounds[param] = (low, high)
            self.bounds.append((low, high))

        self.bo = BayesianOptimization(
            f=self._objective_function,
            pbounds=pbounds,
            random_state=1,
            verbose=2
        )
        
        log.info("贝叶斯优化器初始化完成")

    def _get_optimal_params(self):
        """获取优化后的最优参数"""
        self.bo.maximize(
            init_points=self.size,
            n_iter=self.iters
        )
        
        # 获取最优参数
        best_params = self.bo.max['params']
        return best_params

    def run(self, realtime:dict, target_load:float):
        """
        运行负荷控制系统
        
        :param realtime: 当前的实时运行参数
        :param target_load: 目标负荷 (MW)
        """
        self.target_load = target_load
        log.info(f"启动负荷控制系统: 目标负荷 = {target_load} MW")
        self.model._check_model()
        start = time.time()
        self._init_bayesian_optimizer(realtime)
        
        log.info(f"初始负荷: {realtime[settings.y_params[0]]:.2f} MW (目标: {target_load:.2f} MW)")
        best_params = self._get_optimal_params()
        optimized_x = [best_params[p] for p in self.x]

        log.info(
                f"当前负荷: {realtime[settings.y_params[0]]:.2f} MW | "
                f"目标负荷: {self.target_load:.2f} MW | "
                f"优化预测：{self.model.predict(np.array(optimized_x).reshape(1,-1))} MW"
            )
        log.info(f"贝叶斯优化耗时：{(time.time()-start)*1000:.2f}s")

        return best_params