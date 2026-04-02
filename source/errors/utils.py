ERROR_MESSAGE_MAP = {
    "greater_than": "必须大于{min}",
    "greater_than_equal": "必须大于等于{min}",
    "less_than": "必须小于{max}",
    "less_than_equal": "必须小于等于{max}",
    "multiple_of": "必须是{multiple}的倍数",
    "too_short": "长度必须大于{min_length}",
    "too_long": "长度必须小于{max_length}",
}

def validation_exception_format(error) -> str:
    error_type = error["type"]
    ctx = error["ctx"]
    
    msg_template = ERROR_MESSAGE_MAP.get(error_type, "参数错误: {type}")

    if "{min}" in msg_template:
        if error_type == "greater_than":
            value = ctx.get("gt", "")
        elif error_type == "greater_than_equal":
            value = ctx.get("ge", "")
        else:
            value = ctx.get("min", "")
        msg = msg_template.replace("{min}", str(value))

    elif "{max}" in msg_template:
        if error_type == "less_than":
            value = ctx.get("lt", "")
        elif error_type == "less_than_equal":
            value = ctx.get("le", "")
        else:
            value = ctx.get("max", "")
        msg = msg_template.replace("{max}", str(value))

    elif "{multiple}" in msg_template:
        msg = msg_template.replace("{multiple}", str(ctx.get("multiple", "")))

    else:
        msg = msg_template.replace("{type}", error_type)
    
    field = error["loc"][-1]
    error_message = f"{field}: {msg} "
    return error_message