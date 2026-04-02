import time
import psutil
from source.core.globals import Global
from datetime import timedelta


# previous_cpu = 0
# previous_mem = 0
# previous_time = time.time()

def update_system_message(global_instance:Global) -> None:

    # global previous_cpu, previous_mem, previous_time
    system_status = global_instance.system
    previous_time = system_status["previous_time"]
    previous_cpu = system_status["previous_cpu"]
    previous_mem = system_status["previous_mem"]
    system_start = system_status["system_start"]

    cpu_usage = psutil.cpu_percent(interval=0.5)
    
    mem = psutil.virtual_memory()
    memory_used = round(mem.used / (1024 ** 3), 2)
    memory_total = round(mem.total / (1024 ** 3), 2)
    
    current_time = time.time()
    time_diff = current_time - previous_time

    app_uptime_seconds = current_time - system_start.timestamp()
    uptime = str(timedelta(seconds=int(app_uptime_seconds))).replace(",", "")
    
    if time_diff > 0:
        cpu_trend = round(cpu_usage - previous_cpu, 2)
        memory_trend = round(memory_used - previous_mem, 2)
    else:
        cpu_trend = 0.0
        memory_trend = 0.0
    
    previous_cpu = cpu_usage
    previous_mem = memory_used
    previous_time = current_time

    global_instance.update_system(
        {
            "uptime": uptime,
            "cpu_usage": cpu_usage,
            "cpu_trend": cpu_trend,
            "memory_used": memory_used,
            "memory_total": memory_total,
            "memory_trend": memory_trend,
            "previous_time": previous_time,
            "previous_cpu": previous_cpu,
            "previous_mem": previous_mem
        }
    )

    return 

def check_redis_database_health(global_instance:Global) -> bool:
    """检查数据库连接状态"""
    from source import redis_service
    if redis_service.check_connection():
        global_instance.update_healthy({"redise_connnect_success": True})
    else:
        global_instance.update_healthy({"redise_connnect_success": False})