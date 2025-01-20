from numpy import (
    int8,
    int16,
    int32,
    int64,
    float16,
    float32,
    float64,
    iinfo,
    finfo,
    log10,
    sign,
)
from datetime import datetime, timedelta
from time import perf_counter_ns
from functools import wraps

# def track_all_methods_call_time(cls:object):
#     """create a decorator that will track the total time spent in each method of a class
#     and store it in the class attribute 'total_call_time'

#     Returns:
#         _type_: _description_
#     """
#     orig_init = cls.__init__
#     @wraps(orig_init)
#     def new_init(self, *args, **kwargs):
#         orig_init(self, *args, **kwargs)
#         for attr in dir(cls):
#             if callable(getattr(cls, attr)) and not attr.startswith("__"):
#                 orig_func = getattr(cls, attr)
#                 wrapped_func = time_method(orig_func)
#                 setattr(cls, attr, wrapped_func)
#     cls.__init__ = new_init
#     return cls


def time_method(method):
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        start = perf_counter_ns()
        result = method(self, *args, **kwargs)
        end = perf_counter_ns()
        exec_time = end - start
        
        cls = type(self).__base__ if type(self).__base__ is not object else type(self)

        if not hasattr(cls, "total_call_time"):
            setattr(cls, "total_call_time", 0)
        cls.total_call_time += exec_time
        return result

    return wrapper


def format_time(seconds: float) -> str:
    return f"{datetime.min + timedelta(seconds=abs(seconds)):%H:%M:%S}"


def efficient_number(num):
    # Check if the number is an integer
    if isinstance(num, str):
        num = num.strip()
        num = int(num) if num.isdigit() else float(num)
    if isinstance(num, int):
        # Convert to the most efficient integer type based on the value range
        if iinfo(int8).min <= num <= iinfo(int8).max:
            return int8(num)
        elif iinfo(int16).min <= num <= iinfo(int16).max:
            return int16(num)
        elif iinfo(int32).min <= num <= iinfo(int32).max:
            return int32(num)
        else:
            return int64(num)
    # Check if the number is a float
    elif isinstance(num, float):
        # Convert to the most efficient float type based on the precision needed
        if finfo(float16).min <= num <= finfo(float16).max:
            return float16(num)
        elif finfo(float32).min <= num <= finfo(float32).max:
            return float32(num)
        else:
            return float64(num)

    # Return the original number if it's not int or float
    return num


def calc_throttle(throttle: float) -> int:
    throttle = max(0, min(1, throttle))
    return int(throttle * 2000 - 1000)


def get_tollerance(num: float) -> int:
    try:
        magnitude = int(log10(abs(num)))
    except ValueError: return 10**0
    if magnitude > 0:
        return 10**0
    else:
        return 10**(magnitude - 1)


id_2_icao = {
    "Airbus A220-300": "BCS3",
    "Airbus A319": "A319",
    "Airbus A320": "A320",
    "Airbus A321": "A321",
    "Airbus A330-300": "A333",
    "Airbus A330-900": "A339",
    "Airbus A350": "A359",
    "Airbus A380": "A388",
    "Boeing 737-700": "B737",
    "Boeing 737-8 MAX": "B38M",
    "Boeing 737-800": "B738",
    "Boeing 737-900": "B739",
    "Boeing 747-200": "B742",
    "Boeing 747-400": "B744",
    "Boeing 747-8": "B748",
    "Boeing 757-200": "B752",
    "Boeing 777-200ER": "B772",
    "Boeing 777-200LR": "B77L",
    "Boeing 777-300ER": "B77W",
    "Boeing 777F": "B77F",
    "Boeing 787-8": "B788",
    "Boeing 787-9": "B789",
    "Boeing 787-10": "B78X",
    "Bombardier CRJ-200": "CRJ2",
    "Bombardier CRJ-700": "CRJ7",
    "Bombardier CRJ-900": "CRJ9",
    "Bombardier CRJ-1000": "CRJX",
    "Embraer E175": "E175",
    "Embraer E190": "E190",
    "McDonnell Douglas MD-11": "MD11",
}
