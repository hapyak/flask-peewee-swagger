
def first(list, exception=None):
    match = list[0] if list else None
    if match:
        return match
    elif exception:
        raise exception()
    else:
        return None
