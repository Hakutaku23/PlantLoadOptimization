import time
import redis
import taosrest
import pandas as pd
from datetime import datetime, timedelta
from source.errors.base import RedisConnectionError, TDengineConnectionError
from source.utils.tools import format_dataframe, fill_dataframe
from source import log, settings
from typing import List, Dict


class RedisService:

    def __init__(self, config:dict, auto_connect:bool=True) -> None:
        """
        初始化Redis连接服务
        :param config: 连接配置字典，包含url, user, password, database
        :param auto_connect: 是否自动连接，默认开启
        """
        self.host = config.get("host", "localhost")
        self.port = config.get("port", 6379)
        self.password = config.get("password", None)
        self.db = config.get("db", 0)
        self.max_retries = config.get("max_retries", 3)
        self.retry_delay = config.get("retry_delay", 2)

        if auto_connect:
            self._connect() 
            connect_status = self.connection_status()
            log.info("✅ Redis连接成功!")
            log.info(f"  • 服务器: {self.host}:{self.port} (DB {self.db})")
            log.info(f"  • 响应时间: {connect_status['response_time']}")
            log.info(f"  • Redis版本: {connect_status['server_info']['version']}")
            log.info(f"  • 已连接客户端: {connect_status['server_info']['connected_clients']}")
        else:
            self.redis_connection = None

    def connection_status(self) -> Dict[str, str]:

        self._ensure_connection()
        server_info = self.redis_connection.info()
        status = {
            'host': self.host,
            'port': self.port,
            'db': self.db,
            'connected': False,
            'error': None,
            'response_time': None,
            'server_info': None
        }
        status['connected'] = True
        status['response_time'] = f"{self.response_time:.2f} ms"
        status['server_info'] = {
            'version': server_info.get('redis_version', 'N/A'),
            'uptime': server_info.get('uptime_in_seconds', 'N/A'),
            'connected_clients': server_info.get('connected_clients', 'N/A')
        }

        return status

    def _connect(self):

        try:
            start_time = time.time()
            self.redis_connection = redis.Redis(
                host=self.host,
                port=self.port,
                password=self.password,
                db=self.db,
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5
            )
            self.redis_connection.ping()
            self.response_time = (time.time() - start_time) * 1000
        except redis.ConnectionError as e:
            error_msg = f"❌ Redis连接失败: {str(e)}"
            log.error(error_msg)
            raise RedisConnectionError(error_msg, {
                "host": self.host,
                "port": self.port,
                "db": self.db
            }) from e
        except Exception as e:
            error_msg = f"❌ Redis初始化异常: {str(e)}"
            log.error(error_msg)
            raise RedisConnectionError(error_msg, {
                "host": self.host,
                "port": self.port,
                "db": self.db
            }) from e

    def _ensure_connection(self) -> None:

        retries = 0
        while retries < self.max_retries:
            if self.redis_connection and self.redis_connection.ping():
                return
            
            log.warning(f"Redis连接已断开，尝试第 {retries+1}/{self.max_retries} 次重连...")
            try:
                self._connect()
                return
            except RedisConnectionError as e:
                retries += 1
                if retries < self.max_retries:
                    log.info(f"重连失败，等待 {self.retry_delay} 秒后重试...")
                    time.sleep(self.retry_delay)
                else:
                    log.critical(f"Redis重连失败，已达到最大重试次数 {self.max_retries}")
                    log.error("❌ Redis连接失败")
                    raise

    def check_connection(self) -> bool:

        if self.redis_connection and self.redis_connection.ping():
            return True
        else :
            return False

    def client(self, tags:List[str]) -> Dict[str, float]:

        self._ensure_connection()
        if not tags:
            return {"data": {}}
        try:
            with self.redis_connection.pipeline() as pipe:
                for key in tags:
                    pipe.get(key)
                res = pipe.execute()
            results = dict(zip(tags, res))
            return results
        except Exception as e:
            log.error(f"⚠️ 数据获取错误: {str(e)}")

        return None
    
    def client_backend(self, tags:List[str]) -> Dict[str, float]:

        self._ensure_connection()
        if not tags:
            return {"data": {}}
        try:
            prefix = f"{settings.namespace}:"
            clean_tags = [tag.replace(prefix, "", 1) for tag in tags]
            
            with self.redis_connection.pipeline() as pipe:
                for key in tags:
                    pipe.get(key)
                res = pipe.execute()
            results = dict(zip(clean_tags, res))
            return results
        except Exception as e:
            log.error(f"⚠️ 数据获取错误: {str(e)}")
            return {"data": {}}

    def write(self, tags:Dict[str, float]) -> Dict[str, str]:
        
        self._ensure_connection()
        if not tags:
            return {"status": "无效字典"}
        try:
            with self.redis_connection.pipeline() as pipe:
                for key, value in tags.items():
                    pipe.set(key, value)
                pipe.execute()
            return {"status": f"✅ 批量写入成功：{len(tags)}个键值对"}
        except Exception as e:
            log.error(f"❌ 回写发生未知错误: {str(e)}")
            return {"status": f"❌ 回写发生未知错误: {str(e)}"}


class TDengineService:
    def __init__(self, config: dict) -> None:
        """
        初始化TDengine连接服务
        :param config: 连接配置字典，包含url, user, password, database
        """
        # 提取配置参数
        self.url = config.get("url", "http://localhost:6041")
        self.user = config.get("user", "root")
        self.password = config.get("password", "taosdata")
        self.database = config.get("database", "test")
        self.table_name = config.get("table_name", "table_name")
        self.max_retries = config.get("max_retries", 3)
        self.retry_delay = config.get("retry_delay", 2)
        self.conn = None

    def _connect(self) -> None:
        """建立TDengine连接"""
        try:
            start_time = time.time()
            self.conn = taosrest.connect(
                url=self.url,
                user=self.user,
                password=self.password,
                database=self.database,
                timezone="Asia/Shanghai"
            )
            self.response_time = (time.time() - start_time) * 1000
            log.info("✅ TDengine连接成功!")
            log.info(f"  • 响应时间: {self.response_time:.2f}ms")
            log.info(f"  • 服务器: {self.url} (DB {self.database})")
        except Exception as e:
            error_msg = f"❌ TDengine连接失败: {str(e)}"
            log.error(error_msg)
            raise TDengineConnectionError(error_msg, {
                "url": self.url,
                "database": self.database
            }) from e

    def _ensure_connection(self) -> None:
        """确保连接有效，必要时重连"""
        retries = 0
        while retries <= self.max_retries:
            if self.conn is not None:
                return
            try:
                self._connect()
                return
            except TDengineConnectionError as e:
                retries += 1
                if retries < self.max_retries:
                    log.info(f"❌ 数据库连接失败，等待 {self.retry_delay} 秒后重试...")
                    time.sleep(self.retry_delay)
                else:
                    log.critical(f"TDengine重连失败，已达到最大重试次数 {self.max_retries}")
                    log.error("❌ TDengine连接失败")
                    raise

    def _create_dataframe(self, data, columns) -> pd.DataFrame:

        df = pd.DataFrame(data, columns=columns)
        df_wide = df.pivot_table(
            index='ts',
            columns='point_code',
            values='point_value',
            aggfunc='first'
        ).reset_index()

        df_wide.columns.name = None
        df_wide.rename(columns={'ts': 'ts'}, inplace=True)

        return df_wide

    def get_history_data(self, tags: list[str], 
                        end_time: datetime = None, 
                        start_time: datetime = None) -> pd.DataFrame:
        if not isinstance(tags, list):
            raise TypeError("标签必须为列表形式")
        
        if end_time is None:
            end_time = datetime.now()
        if start_time is None:
            start_time = datetime.now() - timedelta(seconds=100)
        else:
            start_time = start_time - timedelta(seconds=10)
        
        if start_time > end_time:
            raise ValueError("开始时间不得晚于结束时间")
        
        # 格式化时间字符串（TDengine要求格式: YYYY-MM-DD HH:MM:SS）
        end_time_str = end_time.strftime("%Y-%m-%d %H:%M:%S")
        start_time_str = start_time.strftime("%Y-%m-%d %H:%M:%S")

        if len(tags) > 1:
            point_code_conditions = ", ".join([f"'{code}'" for code in tags])
            sql = f"SELECT ts, point_value, point_code FROM {self.table_name} WHERE point_code IN ({point_code_conditions}) AND ts >= '{start_time_str}' AND ts <= '{end_time_str}'"
        elif len(tags) == 1:
            sql = f"SELECT ts, point_value, point_code FROM {self.table_name} WHERE point_code='{tags[0]}' AND ts >= '{start_time_str}' AND ts <= '{end_time_str}'"
        else:
            raise ValueError("至少提供一个tag")
        
        try:
            self._ensure_connection()
            log.debug(f"执行TDengine查询: {sql}")
            cursor = self.conn.cursor()
            cursor.execute(sql)
            col_names = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            
            # print(f"查询到 {len(rows)} 条数据：")
            # print("=" * 65)
            # print(f"{'时间戳':<25} | {'数据值':<15} | {'点位代码':<25}")
            # print("=" * 65)
            
            # for row in rows:
            #     ts, point_value, point_code = row
            #     print(f"{str(ts):<25} | {point_value:<15} | {point_code:<25}")
            
            if not rows:
                return pd.DataFrame(columns=col_names)
            df = self._create_dataframe(rows, col_names)
            df = format_dataframe(df)
            df = fill_dataframe(df)

            return df
            
        except Exception as e:
            error_msg = f"❌ TDengine查询失败: {str(e)}"
            log.error(error_msg)
            raise Exception(error_msg)
        finally:
            self.close()

    def close(self) -> None:
        """关闭连接"""
        if self.conn is not None:
            self.conn.close()
            log.info("TDengine连接已关闭")
        self.conn = None