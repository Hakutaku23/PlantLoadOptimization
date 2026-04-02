import uvicorn
from source.logger import Logger
from pathlib import Path
from source.core.globals import Global, SystemStatus
from source.scheduler.core import SchedulerManager
from source import settings, log
from source.routers import model
from fastapi import FastAPI, Response, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

app = FastAPI()

host = settings.settings["fastapi"].get("host", "0.0.0.0")
port = settings.settings["fastapi"].get("port", 8000)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(model.router, prefix="/open-api/model", tags=["model"])

api_logger = Logger(__name__, log_path=Path(settings.settings["logger"]["path"]), log_file=Path("fastapi.log"), config=settings.settings["logger"]["api"]).logger
@app.middleware("http")
async def log_requests(request: Request, call_next):
    response: Response = await call_next(request)
    x_forwarded_for = request.headers.get("X-Forwarded-For")
    if x_forwarded_for:
        client_ip = x_forwarded_for.split(",")[0].strip()
    else:
        client_ip = request.client.host
    api_logger.info(f"Client: {client_ip}, Method: {request.method}, Path: {request.url.path}, Status: {response.status_code}")
    return response

@app.get("/")
def read_root():
    return JSONResponse(
        content="Created By FastAPI. PSELAB ChongQing China",
        status_code=status.HTTP_200_OK
    )

if __name__ == "__main__":

    global_instance = Global()

    scheduler = SchedulerManager(settings.settings, global_instance=global_instance)
    scheduler.start()   

    global_instance.set_status(SystemStatus.RUNNING)

    from source.core.worker import start_workers
    log.info("🚀 FastAPI应用初始化，添加监听进程...")
    start_workers(settings.settings["fastapi"]["workers"])

    uvicorn.run("main:app", host=host, port=port)
    log.info("🛑 FastAPI应用停止，已清理监听进程，全部进程退出！")

    # import time
    # import pandas as pd
    # from sklearn.model_selection import train_test_split
    # from source.scheduler.tools import calculate_bias
    # from source.utils.optimize import LoadControlSystem
    # from source import ann_model, log

    # data = pd.read_csv(settings.settings["data"]["path"])
    # seed = settings.settings.get("seed", 42)
    # X = data[settings.settings["data"]["x"]].values
    # y = data[settings.settings["data"]["y"]].values

    # X_data, X_test, y_data, y_test  = train_test_split(X, y, test_size=0.2, random_state=seed)
    # lds = LoadControlSystem(ann_model, settings.settings)
    # test_data = [0.0,130.8984385172526,1394.3541178385417,7.252910614013672,699.0874226888021,698.584375,12.8397216796875,6.966046142578124,6.950912475585938,7.078225708007813,6.94833984375,0.0,-15.1090576171875,20.931272379557292,239.187119547526]
    # test_realtime_data = {}
    # for i in range(len(settings.x_params)):
    #     test_realtime_data[settings.x_params[i]] = test_data[i]
    # test_realtime_data[settings.y_params[0]] = test_data[-1]
    # import random

    # while True:
    #     for i in range(X_test.shape[0]):
    #         x = X_test[i]
    #         y = y_test[i]
    #         pred = ann_model.predict(x)
    #         pred = pred.ravel()[0]
    #         print(f"真实值：{y}，模型预测值：{pred}")
    #         if i == X_test.shape[0] -1 :
    #             i = 0
    #         time.sleep(1)
    #     time.sleep(5)
    #     params = lds.run(test_realtime_data, test_data[-1]+random.randint(1, 10))
    #     params = calculate_bias(test_realtime_data, params)
    #     log.info(f"操作量偏置：{params}")