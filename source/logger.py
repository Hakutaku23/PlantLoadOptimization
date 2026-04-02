import logging
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from pathlib import Path
import re


class Logger:
    def __init__(
        self,
        name: str,
        log_path: Path = Path("./logs"),
        log_file: Path = Path("app.log"),
        config: dict = None,
    ):
        default_config = {
            "rotation_type": "size",  # 轮转类型: "size" 或 "time"
            "max_bytes": 10,          # 大小轮转: 文件最大大小(MB)
            "when": "D",              # 时间轮转: 轮转时间单位
            "interval": 7,            # 时间轮转: 间隔天数
            "backup_count": 4,        # 最多保留的备份文件数
            "level": "DEBUG",         # 日志记录等级
        }

        if config is not None:
            default_config.update(config)

        self.rotation_type = default_config["rotation_type"].lower()
        self.max_bytes = default_config["max_bytes"]
        self.when = default_config["when"].upper()
        self.interval = default_config["interval"]
        self.backup_count = default_config["backup_count"]
        self.level = default_config["level"].upper()

        # 验证参数
        if self.rotation_type not in ["size", "time"]:
            raise ValueError("rotation_type 必须是 'size' 或 'time'")
            
        if self.backup_count <= 0:
            raise ValueError("backup_count 必须是大于 0 的整数")

        level_map = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL,
        }
        if self.level not in level_map:
            raise ValueError(f"无效的 'level' 属性: {self.level}. 可用等级: {level_map.keys()}")
        self.level = level_map[self.level]

        self.logger = logging.getLogger(name)
        
        # 确保logger只配置一次（防止重复添加handler）
        if not self.logger.handlers:
            self.logger.setLevel(self.level)

            if not log_path.exists():
                log_path.mkdir(parents=True, exist_ok=True)

            log_full_path = log_path / log_file

            if self.rotation_type == "size":
                # 大小轮转配置
                if not isinstance(self.max_bytes, int) or self.max_bytes <= 0:
                    raise ValueError("max_bytes 必须是大于 0 的整数")
                
                max_bytes_calc = self.max_bytes * 1024 * 1024  # 转换为字节
                max_bytes_calc = min(25 * 1024 * 1024, max_bytes_calc)  # 限制最大25MB
                
                handler = RotatingFileHandler(
                    log_full_path,
                    maxBytes=max_bytes_calc,
                    backupCount=self.backup_count,
                    encoding="utf-8",
                )
                
            else:  # time rotation
                # 时间轮转配置
                if self.interval <= 0:
                    raise ValueError("interval 必须是大于 0 的整数")
                    
                handler = TimedRotatingFileHandler(
                    filename=log_full_path,
                    when=self.when,
                    interval=self.interval,
                    backupCount=self.backup_count,
                    encoding="utf-8",
                )
                
                # 设置后缀为按时间轮转
                handler.suffix = "%Y-%m-%d_%H-%M-%S"
                
                # 设置匹配模式，用于删除旧文件
                handler.extMatch = re.compile(r"^\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}$")

            handler.setLevel(self.level)

            # 设置日志格式
            formatter = logging.Formatter(
                "[%(asctime)s - %(levelname)s - %(module)s - %(funcName)s] %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
            handler.setFormatter(formatter)
            
            self.logger.addHandler(handler)

    def debug(self, message):
        self.logger.debug(message, stacklevel=2)

    def info(self, message):
        self.logger.info(message, stacklevel=2)

    def warning(self, message):
        self.logger.warning(message, stacklevel=2)

    def error(self, message):
        self.logger.error(message, stacklevel=2)

    def critical(self, message):
        self.logger.critical(message, stacklevel=2)