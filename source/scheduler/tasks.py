from source.scheduler.tools import get_realtime_data, calculate_bias, calculate_benchmark
from source.core.globals import Global
from source import ann_model, redis_service, log, settings, load_control_system


def realtime_predict(global_instance:Global):

    try:
        x_data, y_data, _ = get_realtime_data(global_instance)
        if x_data is None:
            log.error("实时数据获取失败，实时预测跳过")
            return
        pred = ann_model.predict(x_data)
        pred = pred.ravel()[0]
        redis_service.write({settings._format_params("30AMBFHTJ_001"):str(pred)})

    except Exception as e:
        log.error(f"实时预测任务失败：{str(e)}")

    return

def optimize(global_instance:Global):

    try:
        _, _, realtime = get_realtime_data(global_instance, save=False)
        if realtime is None:
            log.error("实时数据获取失败，优化跳过")
            return
        # 负荷调节率
        load_regulation_rate = realtime[settings.settings["optimize"]["target"]["load_regulation_rate"]]
        target_load = realtime[settings.settings["optimize"]["target"]["target_load"]]
        currect_load = realtime[settings.settings["optimize"]["target"]["currect_load"]]
        if abs(currect_load - target_load) < 1:
            log.info(f"负荷接近，优化跳过")
            return
        if currect_load < target_load:
            toward_target_load = currect_load + load_regulation_rate
        else:
            toward_target_load = currect_load - load_regulation_rate
        control_params = load_control_system.run(realtime, toward_target_load)
        # params = calculate_bias(realtime, control_params)
        params = calculate_benchmark(control_params)
        redis_service.write(params)
    except Exception as e:
        log.error(f"实时优化任务失败：{e}")
    return