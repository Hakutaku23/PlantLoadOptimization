import time
import datetime
import multiprocessing
from enum import Enum


class SystemStatus(Enum):
    IDLE = 0
    RUNNING = 1
    WARNING = 2
    ERROR = 3
    TRAINING = 4

class Global:
    _instance = None
    _manager = None
    
    def __new__(cls):
        if cls._instance is None:
            if multiprocessing.current_process().name == "MainProcess":
                cls._manager = multiprocessing.Manager()
                cls._instance = super(Global, cls).__new__(cls)
                cls._instance._shared_dict = cls._manager.dict()
                cls._instance._shared_status = cls._manager.Value('i', SystemStatus.IDLE.value)
                cls._instance._shared_healthy = cls._manager.dict()

                cls._instance._shared_dict.update({
                    "uptime": "0",
                    "cpu_usage": 0.0,
                    "cpu_trend": 0.0,
                    "memory_used": 0.0,
                    "memory_total": 0.0,
                    "memory_trend": 0.0,
                    "system_start": datetime.datetime.now(),
                    "previous_time": time.time(),
                    "previous_cpu": 0.0,
                    "previous_mem": 0.0,
                    "task_status": {}
                })
                cls._instance._shared_healthy.update(
                    {
                        "redise_connnect_success": False,
                        "database_error": False,
                    }
                )
            else:
                raise RuntimeError("全局变量必须在main函数中初始化！")
        return cls._instance

    @property
    def healthy(self):
        return self._shared_healthy

    @property
    def system(self):
        """返回共享字典 (安全访问)"""
        return self._shared_dict

    @property
    def status(self):
        """返回系统状态 (自动转换为Enum)"""
        return SystemStatus(self._shared_status.value)

    def set_status(self, new_status: SystemStatus):
        """安全设置状态 (避免直接修改)"""
        self._shared_status.value = new_status.value

    def update_system(self, system:dict):
        """安全更新系统状态 (原子操作)"""
        for key, value in system.items():
            self._shared_dict[key] = value

    def update_healthy(self, healthy:dict):
        self._shared_healthy.update(healthy)

    @staticmethod
    def get_instance():
        """安全获取实例（子进程直接调用）"""
        return Global()