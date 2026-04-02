import pandas as pd
from typing import List


def format_dataframe(df:pd.DataFrame) -> pd.DataFrame:
    cols = df.columns.tolist()
    dfs:List[pd.DataFrame] = []
    dfs_new:List[pd.DataFrame] = []
    for col in cols[1:]:
        dfs.append(df[[cols[0], col]].copy())
    for d in dfs:
        d[cols[0]] = pd.to_datetime(d[cols[0]])
        d[cols[0]] = d[cols[0]].dt.strftime('%Y-%m-%d %H:%M:%S')
        d = d.dropna()
        d.reset_index(drop=True, inplace=True)
        d.set_index(cols[0], inplace=True)
        if d.index.duplicated().any():
            d = d[~d.index.duplicated(keep='first')]
        dfs_new.append(d)

    df_combined = pd.concat(dfs_new, axis=1)
    return df_combined

def fill_dataframe(df:pd.DataFrame) -> pd.DataFrame:

    if df.empty:
        return df
    df.index = pd.to_datetime(df.index)
    start_time = df.index.min()
    end_time = df.index.max()
    new_index = pd.date_range(start=start_time, end=end_time, freq='s')
    df_resampled = df.reindex(new_index)
    df_interpolated = df_resampled.interpolate(method='time')
    return df_interpolated

def format_tags(tag:str, dtype:str="dcs") -> str:
    if dtype.lower() == "dcs":
        return "DCS_AI_" + tag + "_AV"
    
def use_redis_history() -> None:
    
    from source import system_global, settings
    import numpy as np
    x0, y0 = system_global.realtime_data
    system_global.history_data = [[], []]
    for _ in range(settings.system_config["scheduler"]["tasks"]["step"]):
        noise_x = np.random.normal(0, 0.01 * np.abs(x0), size=len(x0))
        noise_y = np.random.normal(0, 0.01 * np.abs(y0), size=len(y0))

        x_noise = np.clip(x0 + noise_x, 0, None)
        y_noise = np.clip(y0 + noise_y, 0, None)
        
        system_global.history_data[0].append(x_noise)
        system_global.history_data[1].append(y_noise)

# def use_tdengine_history() -> None:

#     from source import system_global, settings, tdengine_service
#     from source.utils.tools import format_tags
#     x_tags = [format_tags(t) for t in settings.model_params["x"]]
#     y_tags = [format_tags(t) for t in settings.model_params["y"]]
#     total = x_tags.copy()
#     total.extend(y_tags)
#     data = tdengine_service.get_history_data(total)
#     data = data.sort_index(ascending=False)
#     if "DCS_AI_TC_2204_AV" not in data.columns:
#         if ("DCS_AI_AMI_TC_2202_AV" in data.columns) and ("DCS_AI_AMI_TC_2203_AV" in data.columns):
#             data["DCS_AI_TC_2204_AV"] = data[["DCS_AI_AMI_TC_2202_AV", "DCS_AI_AMI_TC_2203_AV"]].mean(axis=1)
#     x_array = data[x_tags].copy().values
#     y_array = data[y_tags].copy().values
#     x_array = x_array[:settings.system_config["scheduler"]["tasks"]["step"],:]
#     y_array = y_array[:settings.system_config["scheduler"]["tasks"]["step"],:]
#     x_data = [row for row in x_array]
#     y_data = [row for row in y_array]
#     system_global.history_data = [x_data, y_data]
    
# def init_system() -> None:

#     from source.scheduler.task.periodic import get_redis_data
#     from source import system_global, settings
#     get_redis_data(redis_history=False)

#     if settings.system_config["scheduler"]["tasks"]["redis_history"] and system_global.redise_connnect_success:
#         use_redis_history()
#     elif not settings.system_config["scheduler"]["tasks"]["redis_history"]:
#         from source.database.database import log_event
#         try:
#             use_tdengine_history()
#         except Exception as e:
#             log_event("error", f"TdEngine数据库查询失败：{e}，使用Redis构建历史数据")
#             if system_global.redise_connnect_success:
#                 use_redis_history()
#     else:
#         system_global.history_data = [[], []]
#         from source.database.database import log_event
#         log_event("error", "初始化历史数据库失败！")