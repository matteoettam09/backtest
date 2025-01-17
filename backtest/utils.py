def signum(n):
    if n < 0:
        return -1
    
    if n > 0:
        return 1
    
    return 0


def is_int(value: str):
    try:
        int(value)
        return True
    except ValueError:
        return False


def is_float(value: str):
    try:
        float(value)
        return True
    except ValueError:
        return False


def is_number(value: str):
    return is_int(value) or is_float(value)


def is_blank(value: str):
    return value is None or len(value.strip()) == 0


def ensure_not_blank(value: str, property: str=None) -> str:
    if is_blank(value):
        if property:
            raise ValueError(f"{property} must not be blank")
        else:
            raise ValueError(f"must not be blank")

    return value