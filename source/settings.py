import os
import yaml
from pathlib import Path


CONFIG_DIR = os.path.abspath(os.path.join(os.getcwd(), "config"))
CONFIG_PATH = Path(os.path.join(CONFIG_DIR, "config.yaml"))

class Config:

    def __init__(self):
        
        self.__settings = self._load_yaml(CONFIG_PATH)
        self.__x = self.__settings["data"]["x"]
        self.__y = self.__settings["data"]["y"]
        self.__optimize_param = self.__settings["data"]["oprimize"]
        self.__redis_namespace = self.settings["data"]["namespace"]
        
        redis_x = [self._format_params(p) for p in self.__x]
        redis_y = [self._format_params(p) for p in self.__y]
        redis_optimize = [self._format_params(p) for p in self.__optimize_param]
        self.__redis_params = redis_x.copy()
        self.__redis_params.extend(redis_y)
        self.__redis_params.extend(redis_optimize)

    def _load_yaml(self, file_path:Path) -> dict:

        with open(file_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def _format_params(self, param):
        
        return self.__redis_namespace + f":{param}"

    @property
    def settings(self) -> dict:
        return self.__settings
    
    @property
    def x_params(self) -> list:
        return self.__x
    
    @property
    def y_params(self) -> list:
        return self.__y
    
    @property
    def namespace(self) -> str:
        return self.__redis_namespace
    
    @property
    def redis_params(self) -> list:
        return self.__redis_params

    @property
    def optimize(self) -> list:
        return self.__optimize_param