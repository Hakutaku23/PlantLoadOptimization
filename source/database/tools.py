import time
import json
import pickle
import base64
import numpy as np
from ast import literal_eval
from typing import List, Any, Dict
from source import log
from source.database.service import RedisService


class NumpyEncoder(json.JSONEncoder):
    """自定义JSON编码器，支持numpy数组"""
    
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return {
                '__numpy_array__': True,
                'data': base64.b64encode(pickle.dumps(obj)).decode('utf-8'),
                'dtype': str(obj.dtype),
                'shape': obj.shape
            }
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        return super().default(obj)

class NumpyDecoder(json.JSONDecoder):
    """自定义JSON解码器，支持numpy数组"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(object_hook=self.object_hook, *args, **kwargs)
    
    def object_hook(self, obj):
        if '__numpy_array__' in obj:
            data = base64.b64decode(obj['data'].encode('utf-8'))
            return pickle.loads(data)
        return obj

class RedisDataFormatter:
    """Redis数据格式化工具类（优化版）"""
    
    @staticmethod
    def serialize_complex_data(data: Any) -> str:
        """
        序列化复杂数据结构（包含numpy数组）
        
        Args:
            data: 要序列化的数据
            
        Returns:
            JSON字符串
        """
        try:
            return json.dumps(data, cls=NumpyEncoder, ensure_ascii=False)
        except Exception as e:
            log.error(f"❌ 数据序列化失败: {str(e)}")
            raise
    
    @staticmethod
    def deserialize_complex_data(data_str: str) -> Any:
        """
        反序列化复杂数据结构
        
        Args:
            data_str: JSON字符串
            
        Returns:
            原始数据结构
        """
        try:
            return json.loads(data_str, cls=NumpyDecoder)
        except Exception as e:
            log.error(f"❌ 数据反序列化失败: {str(e)}")
            raise

class RedisDataManager:
    def __init__(self, redis_service: RedisService, namespace: str = "ml_pipeline", windows:dict={}):
        self.redis = redis_service
        self.namespace = namespace
        self.formatter = RedisDataFormatter()
        self.list_length = int(windows.get("size", 30))
        self.list_ttl = int(windows.get("ttl", 30))
    
    def _get_key(self, key: str) -> str:
        """为键添加命名空间前缀"""
        return f"{self.namespace}:{key}"
        
    def store_list(self, temp_list:list) -> bool:

        try:
            key = self._get_key("temp_list")
            if len(temp_list) > self.list_length - 1:
                temp_list.pop(0)
            # o2 = [float(x) for x in o2]
            self.redis.redis_connection.set(key, f"{temp_list}", ex=self.list_ttl)
        except Exception as e:
            log.error(f"❌ 存储实时窗口数据失败: {str(e)}")
            return False
        
    def get_list(self) -> list:

        try:
            key = self._get_key("temp_list")
            value = self.redis.redis_connection.get(key)
            if value:
                value = literal_eval(value)
                # current_list = [float(x) for x in value]
                # current_value = np.mean(value, axis=0)
                return value
            else:
                return []
        except Exception as e:
            log.error(f"❌ 读取实时窗口数据失败: {str(e)}")
            return []
    
    def store_realtime_data(self, history_data: List[List[np.ndarray]]) -> bool:
        """
        优化版：分离元数据与原始数据存储
        1. 元数据（小量）存储到独立键
        2. 原始数据（大量）存储到独立键
        3. 避免序列化大对象时包含冗余元数据
        
        Args:
            history_data: List[list[ndarray], list[ndarray]] 格式的数据
            
        Returns:
            是否存储成功
        """
        try:
            if history_data is None:
                log.warning("⚠️ history_data为None，跳过存储")
                return False
            
            # 构建轻量级元数据（仅结构信息，无原始数据）
            # metadata = self._build_lightweight_metadata(history_data)
            
            # # 存储元数据（小量，普通JSON序列化）
            # metadata_key = self._get_key("realtime:metadata")
            # self.redis.redis_connection.set(
            #     metadata_key, 
            #     json.dumps(metadata, ensure_ascii=False),
            #     ex=600  # 10分钟过期
            # )
            
            # 存储原始数据（大量，使用NumpyEncoder序列化）
            data_key = self._get_key("realtime:data")
            serialized_data = self.formatter.serialize_complex_data(history_data)
            self.redis.redis_connection.set(
                data_key, 
                serialized_data,
                ex=600  # 10分钟过期
            )
            
            # # 仅记录关键元数据（避免打印大对象）
            # log.debug(f"✅ 实时数据存储成功 - "
            #          f"元数据: {metadata['length']}列表, "
            #          f"总元素: {metadata['total_elements']}")
            
            return True
            
        except Exception as e:
            log.error(f"❌ 存储实时数据失败: {str(e)}")
            return False
    
    def _build_lightweight_metadata(self, history_data: List[List[np.ndarray]]) -> Dict:
        """构建轻量级元数据（不包含原始数据）"""
        if not history_data:
            return {
                "type": "history_data",
                "length": 0,
                "total_elements": 0,
                "timestamp": time.time()
            }
        
        total_elements = 0
        for array_list in history_data:
            for arr in array_list:
                total_elements += arr.size
        
        return {
            "type": "history_data",
            "length": len(history_data),
            "total_elements": total_elements,
            "timestamp": time.time(),
            "version": "1.0"
        }
    
    def get_realtime_data(self) -> List[List[np.ndarray]]:
        """
        优化版：直接获取原始数据，避免解析冗余元数据
        """
        try:
            data_key = self._get_key("realtime:data")
            serialized_data = self.redis.redis_connection.get(data_key)
            
            if serialized_data is None:
                log.warning("📭 Redis中未找到实时数据（原始数据）")
                return None
            
            # 直接反序列化原始数据（不经过元数据）
            history_data = self.formatter.deserialize_complex_data(serialized_data)
            
            # 仅记录关键信息（避免大对象日志）
            # metadata = self.get_realtime_metadata()
            # log.debug(f"📥 实时数据读取成功 - "
            #          f"总元素: {metadata.get('total_elements', 0)}")
            
            return history_data
            
        except Exception as e:
            log.error(f"❌ 读取实时数据失败: {str(e)}")
            return None
    
    def get_realtime_metadata(self) -> Dict[str, Any]:
        """
        优化版：直接获取轻量级元数据
        """
        try:
            metadata_key = self._get_key("realtime:metadata")
            metadata_json = self.redis.redis_connection.get(metadata_key)
            
            if metadata_json is None:
                return {}
            
            # 普通JSON解析（无需NumpyDecoder）
            return json.loads(metadata_json)
            
        except Exception as e:
            log.error(f"❌ 读取实时数据元数据失败: {str(e)}")
            return {}