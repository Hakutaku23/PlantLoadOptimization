import uuid
from typing import Dict
from multiprocessing import Queue
from source.core.globals import Global
from source import log


task_queue = Queue()
task_status: Dict[str, str] = {}

def submit_task(name:str) -> str:
    """提交训练任务到队列"""
    task_id = str(uuid.uuid4())
    task_queue.put((task_id, name))
    task_status[task_id] = "queued"
    Global().update_system(system={"task_status": task_status})
    log.info(f"添加任务：{name}，任务id：{task_id}")
    return task_id

def get_task_status(task_id: str) -> str | None:
    """获取任务状态"""
    task_status_global = Global().system["task_status"]
    return task_status_global.get(task_id)