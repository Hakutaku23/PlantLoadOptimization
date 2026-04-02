import time
import pandas as pd
from multiprocessing import Process
from source import settings, log
from source.core.globals import Global, SystemStatus
from source.core.pipeline import task_queue, task_status
from source.model.core import model_train
from sklearn.model_selection import train_test_split


def process_retraining_task(task_id: str):
    """实际训练逻辑（替换为你的训练代码）"""

    log.info(f"模型重新练任务开始，任务id：{task_id[:6]}...")
    global_instance = Global.get_instance()
    data = pd.read_csv(settings.settings["data"]["path"])
    seed = settings.settings.get("seed", 42)
    X = data[settings.settings["data"]["x"]].values
    y = data[settings.settings["data"]["y"]].values

    X_data, X_test, y_data, y_test  = train_test_split(X, y, test_size=0.2, random_state=seed)
    try:
        metrics = model_train(X_data, y_data, X_test, y_test, retrain=True)
    except Exception as e:
        log.error(f"模型重训练任务失败，任务id：{task_id[:6]}...，错误：{e}")
        global_instance.set_status(SystemStatus.RUNNING)
    task_status[task_id] = "completed"
    global_instance.update_system({"task_status": task_status})

def worker():
    """工作进程，持续监听任务队列"""
    while True:
        try:
            task_id, name = task_queue.get()
            if name == "retrain":
                process_retraining_task(task_id)
        except Exception as e:
            log.info(f"工作进程错误: {e}")

def start_workers(num_workers=4):
    """启动多进程工作池"""
    processes = []
    for _ in range(num_workers):
        p = Process(target=worker)
        p.start()
        processes.append(p)
    log.info("📊 正在启动工作进程...")
    for p in processes:
        log.info(f"工作进程PID {p.pid} 正在活动: {p.is_alive()}")
    log.info(f"✅ 已启动 {num_workers} 个工作进程，正在监听任务列表")