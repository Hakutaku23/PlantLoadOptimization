from typing import Dict


class RedisConnectionError(Exception):
    
    def __init__(self, message: str, connection_info: Dict = None):
        self.message = message
        self.connection_info = connection_info or {
            "host": "localhost",
            "port": 6379,
            "db": 0
        }
        super().__init__(self.message)

    def __str__(self):
        return f"RedisConnectionError[{self.connection_info['host']}:{self.connection_info['port']}(DB{self.connection_info['db']})]: {self.message}"
    
class TDengineConnectionError(Exception):

    def __init__(self, message: str, connection_info: Dict = None):
        self.message = message
        self.connection_info = connection_info or {
            "host": "localhost",
            "port": 6379,
            "db": 0
        }
        super().__init__(self.message)

    def __str__(self):
        return f"RedisConnectionError[{self.connection_info['host']}:{self.connection_info['port']}(DB{self.connection_info['db']})]: {self.message}"