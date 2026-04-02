import time
# import functools
# from source import system_global
# from source.database.database import log_event
# from source.scheduler.task.periodic import get_redis_data, system_message_task, cleanup_old_events, remove_report_log_files
# from source.scheduler.task.optimizer import optimization, predict_o2_temp, cal_control_param
# from source.utils.tools import init_system
from source.core.globals import Global
from source.test import model_train_task
from source.utils.system import update_system_message, check_redis_database_health
from source.scheduler.tasks import realtime_predict, optimize
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers.base import STATE_RUNNING
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
from logging import Logger


class SchedulerManager:

    def __init__(self, config: dict, global_instance:Global, job_listener: callable = None, log: Logger = None):
        self.config = config
        self.job_listener = job_listener
        self.scheduler = None
        self.logger = log
        self._manual_jobs_init()
        self.global_instance = global_instance
        # 存储需要手动启动的任务（不立即添加）
        self.started_manual_jobs = set()
        self.max_instances = self.config["scheduler"]["global"]["max_instances"]
    
    def _manual_jobs_init(self):

        self.manual_jobs = [
            # (get_redis_data, IntervalTrigger(seconds=self.config["scheduler"]["tasks"]["realtime"]), "redis_data", "redis_data", "default"),
            # (predict_o2_temp, IntervalTrigger(seconds=self.config["scheduler"]["tasks"]["realtime"]), "predict", "predict", "processpool"),
            # (optimization, IntervalTrigger(seconds=self.config["scheduler"]["tasks"]["interval"]), "optimization", "optimization", "processpool"),
            # (cal_control_param, IntervalTrigger(seconds=self.config["scheduler"]["tasks"]["control"]), "param", "param", "processpool")
            # (test_optimization, IntervalTrigger(seconds=self.config["scheduler"]["tasks"]["interval"]), "test_optimization", "test_optimization", "processpool")
        ]

    def _create_scheduler(self) -> BackgroundScheduler:
        executors = {
            "default": ThreadPoolExecutor(self.config["scheduler"]["global"]["thread"]),
            "processpool": ProcessPoolExecutor(self.config["scheduler"]["global"]["process"]),
        }

        job_defaults = {
            "coalesce": self.config["scheduler"]["global"]["coalesce"],
            "max_instances": self.max_instances
        }

        scheduler = BackgroundScheduler(
            executors=executors,
            job_defaults=job_defaults
        )
        if self.job_listener is not None:
            scheduler.add_listener(self.job_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
        return scheduler

    def _add_initial_jobs(self):
        """添加初始启动的任务（系统监控、数据库清理）"""
        # bound_update = functools.partial(update_system_message, global_instance=self.global_instance)
        # bound_check = functools.partial(check_redis_database_health, global_instance=self.global_instance)
        # bound_realtime = functools.partial(realtime_predict, global_instance=self.global_instance)

        self.log("添加系统监控任务...")
        self.scheduler.add_job(
            func=update_system_message,
            args=[self.global_instance],
            trigger=IntervalTrigger(seconds=int(self.config["scheduler"]["tasks"]["system"])),
            id="system",
            name="系统状态监控",
            replace_existing=True,
            executor="processpool"
        )

        self.log("添加数据库检查任务...")
        self.scheduler.add_job(
            func=check_redis_database_health,
            args=[self.global_instance],
            trigger=IntervalTrigger(seconds=10),
            id="redis",
            name="Redis数据库检查",
            replace_existing=True,
            executor="processpool"
        )

        self.log("添加模型实时预测任务...")
        self.scheduler.add_job(
            func=realtime_predict,
            args=[self.global_instance],
            trigger=IntervalTrigger(seconds=int(self.config["scheduler"]["tasks"]["realtime"])),
            id="realtime",
            name="模型实时预测",
            replace_existing=True,
            executor="processpool"
        )

        self.log("添加模型实时优化任务...")
        optimize_interval = 30 if int(self.config["optimize"]["interval"]) < 30 else int(self.config["optimize"]["interval"])
        self.scheduler.add_job(
            func=optimize,
            args=[self.global_instance],
            trigger=IntervalTrigger(seconds=optimize_interval),
            id="optimize",
            name="模型实时优化",
            replace_existing=True,
            executor="processpool"
        )

        # self.scheduler.add_job(
        #     func=model_train_task,
        #     trigger=IntervalTrigger(minutes=5),
        #     id="model_train_test",
        #     name="model_train_test",
        #     replace_existing=True,
        #     executor="processpool"
        # )
        # self.scheduler.add_job(
        #     func=test_random_forest,
        #     trigger=IntervalTrigger(seconds=int(self.config["scheduler"]["tasks"]["system"])),
        #     id="test",
        #     name="test",
        #     replace_existing=True
        # )
        # self.log("添加数据库事件清理任务...")
        # self.scheduler.add_job(
        #     func=cleanup_old_events,
        #     trigger=CronTrigger(hour=1, minute=0),
        #     id="event_cleanup",
        #     name="Events_Cleanup",
        #     max_instances=1,
        #     misfire_grace_time=300
        # )
        # self.scheduler.add_job(
        #     func=remove_report_log_files,
        #     trigger=CronTrigger(hour=1, minute=0),
        #     id="reposrt_cleanup",
        #     name="Report_Cleanup",
        #     max_instances=1,
        #     misfire_grace_time=300
        # )

    def log(self, msg):
        if self.logger:
            self.logger.info(msg)

    def start(self):
        if self.scheduler is not None:
            return
        self.scheduler = self._create_scheduler()
        self._add_initial_jobs()
        self.scheduler.start()
        self.log("任务调度器启动成功。")

    def start_manual_jobs(self):
        """启动手动控制的任务（通过API调用）"""
        if self.scheduler and self.scheduler.state == STATE_RUNNING:
            # init_system()
            for func, trigger, job_id, name, executor in self.manual_jobs:
                if job_id not in self.started_manual_jobs:
                    self.scheduler.add_job(
                        func=func,
                        trigger=trigger,
                        id=job_id,
                        name=name,
                        executor=executor,
                        max_instances=self.max_instances,
                        replace_existing=True
                    )
                    self.started_manual_jobs.add(job_id) 
            self.log("优化任务已启动。")
            # system_global.optimizer = True
            # system_global._reset_status()
        else:
            # log_event("error", "任务调度器未运行或异常，无法启动优化任务。")
            # system_global._system_error()
            ...

    def restart(self, config: dict) -> bool:
        if self.scheduler and self.scheduler.state == STATE_RUNNING:
            self.scheduler.shutdown(wait=True)
            self.scheduler = None
            time.sleep(0.5)

        temp_config = self.config
        self.config = config

        try:
            self.scheduler = self._create_scheduler()
            self._add_initial_jobs()
            self.scheduler.start()
            self.log("任务调度器重启成功。")
            # system_global._reset_status()
            return True
        except Exception as e:
            self.config = temp_config
            self.scheduler = self._create_scheduler()
            self._add_initial_jobs()
            self.scheduler.start()
            # system_global._reset_status()
            return False

    def shutdown(self):
        """关闭调度器"""
        if self.scheduler and self.scheduler.state == STATE_RUNNING:
            self.scheduler.shutdown(wait=True)
            self.scheduler = None
            # system_global._system_warning()
        else:
            pass
        return True