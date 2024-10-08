def deepcopy(obj):
    if isinstance(obj, dict):
        return {key: deepcopy(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [deepcopy(element) for element in obj]
    elif isinstance(obj, tuple):
        return tuple(deepcopy(element) for element in obj)
    else:
        return obj  # 对于不可变对象，直接返回（如字符串、数字）