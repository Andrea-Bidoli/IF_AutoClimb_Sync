from numpy import int8, int16, int32, int64, float16, float32, float64, iinfo, finfo, sqrt
from datetime import datetime, timedelta
from time import perf_counter_ns
from functools import wraps

from .convertion import *

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
        cls=type(self).__base__
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

def calc_throttle(throttle:float) -> int:
    throttle = max(0, min(1, throttle))
    return int(throttle * 2000 - 1000)

def in_range(value:float, target:float, tollerance:float=1) -> bool:
    """in range, tollerance is for 1 kts

    Args:
        value (float): get value
        target (float): target value
        tollerance (float, optional): tollerance. Defaults to 1.

    Returns:
        bool: True if value is in range
    """
    return target-tollerance <= value <= target+tollerance