from source.core.globals import Global, SystemStatus
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from source.core.pipeline import submit_task


router = APIRouter()

@router.get("/retrain")
async def retrain_model():

    global_instance = Global.get_instance()
    if global_instance.status is SystemStatus.TRAINING:
        return JSONResponse(
            content="模型训练中，重新练任务添加失败！",
            status_code=status.HTTP_200_OK
        )
    task_id = submit_task("retrain")
    return JSONResponse(
        content=f"添加模型重训练任务成功！任务id:{task_id}",
        status_code=status.HTTP_200_OK
    )
    