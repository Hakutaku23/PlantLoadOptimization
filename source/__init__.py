import os

from datetime import datetime, timezone
system_start = datetime.now(timezone.utc)
from source.settings import Config
from pathlib import Path

settings = Config()

CWD = os.getcwd()
model_settings = settings.settings.get("model")
MODEL_PATH = Path(os.path.join(os.getcwd(), model_settings.get("path", "models")))
if not os.path.exists(MODEL_PATH):
    os.makedirs(MODEL_PATH)

from . import logger
log = logger.Logger(__name__, log_path=Path(settings.settings["logger"]["path"]), config=settings.settings["logger"]["app"])

from source.model.model import Module
ann_model = Module(MODEL_PATH, model_settings["type"])

from . import core
from . import database
from . import errors
from . import model
from . import scheduler
from . import utils

from .database.service import RedisService, TDengineService
from source.core.globals import Global
try:
    redis_service = RedisService(settings.settings["redis"])
    Global().update_healthy({"redise_connnect_success": True})
except Exception as e:
    redis_service = RedisService(settings.settings["redis"], auto_connect=False)
tdengine_service = TDengineService(settings.settings["taos"])

from .database.tools import RedisDataManager
redis_data_manager = RedisDataManager(redis_service, windows=settings.settings["windows"])

from .utils.optimize import LoadControlSystem
load_control_system = LoadControlSystem(ann_model, settings.settings)