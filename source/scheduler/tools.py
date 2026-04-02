from numpy import mean
from source import redis_service, log, settings, redis_data_manager
from source.core.globals import Global


def get_realtime_data(global_instance:Global, save=True):

    if not global_instance.healthy["redise_connnect_success"]:
        log.error("Redis数据库连接失败，实时任务暂停！")
        return None,None,None
    
    realtime_data = redis_service.client_backend(settings.redis_params)
    x_data = []
    y_data = []
    errors = 0
    errmsg = []
    for k, v in realtime_data.items():
        try:
            value = float(v) if v is not None else -99.0
            realtime_data[k] = value
        except Exception as e:
            errors += 1
            if str(e) not in errmsg:
                errmsg.append(str(e))
            realtime_data[k] = -99.0
    for v in settings.x_params:
        x_data.append(realtime_data[v])
    for v in settings.y_params:
        y_data.append(realtime_data[v])

    if errors != 0:
        log.error(errmsg)
    if x_data.count(-99) > len(x_data) / 2:
        global_instance.update_system({"database_error": True})
    else:
        global_instance.update_system({"database_error": False})
    # x_data = np.array(x_data, dtype=np.float64)
    # y_data = np.array(y_data, dtype=np.float64)
    x_windows = redis_data_manager.get_list()
    if x_windows:
        x_windows.append(x_data)
    if save:
        redis_data_manager.store_list(x_windows)
    x_data = mean(x_windows, axis=0)

    return x_data, y_data, realtime_data

def calculate_bias(currect_params, target_params):

    bias_total_coal = target_params["30HFB00AA101DSP"] - currect_params["30HFB00AA101DSP"]
    bias_total_air = target_params["30GAMD"] - currect_params["30GAMD"]
    bias_total_o2 = target_params["30O2"] - currect_params["30O2"]
    bias_total_water = target_params["30LAB30CF900ALL"] - currect_params["30LAB30CF900ALL"]
    bias_total_stream = target_params["11DTP"] - currect_params["11DTP"]
    bias_total_wind = mean([target_params["30HLA10CP101"], target_params["30HLA10CP102"], target_params["30HLA20CP101"], target_params["30HLA20CP102"]]) - mean([currect_params["30HLA10CP101"], currect_params["30HLA10CP102"], currect_params["30HLA20CP101"], currect_params["30HLA20CP102"]])
    bias_total_overtemp = target_params["3OVERHEAT"] - currect_params["3OVERHEAT"]

    write_back = {
        "DCS3:30AMBFHTJ_002": str(bias_total_coal),
        "DCS3:30AMBFHTJ_003": str(bias_total_air),
        "DCS3:30AMBFHTJ_004": str(bias_total_o2),
        "DCS3:30AMBFHTJ_005": str(bias_total_water),
        "DCS3:30AMBFHTJ_006": str(bias_total_stream),
        "DCS3:30AMBFHTJ_007": str(bias_total_wind),
        "DCS3:30AMBFHTJ_008": str(bias_total_overtemp) 
    }
    return write_back

def calculate_benchmark(target_params):

    bias_total_coal = target_params["30HFB00AA101DSP"] 
    bias_total_air = target_params["30GAMD"]
    bias_total_o2 = target_params["30O2"] 
    bias_total_water = target_params["30LAB30CF900ALL"] 
    bias_total_stream = target_params["11DTP"]
    bias_total_wind = mean([target_params["30HLA10CP101"], target_params["30HLA10CP102"], target_params["30HLA20CP101"], target_params["30HLA20CP102"]])
    bias_total_overtemp = target_params["3OVERHEAT"]

    write_back = {
        "DCS3:30AMBFHTJ_002": str(bias_total_coal),
        "DCS3:30AMBFHTJ_003": str(bias_total_air),
        "DCS3:30AMBFHTJ_004": str(bias_total_o2),
        "DCS3:30AMBFHTJ_005": str(bias_total_water),
        "DCS3:30AMBFHTJ_006": str(bias_total_stream),
        "DCS3:30AMBFHTJ_007": str(bias_total_wind),
        "DCS3:30AMBFHTJ_008": str(bias_total_overtemp) 
    }
    return write_back