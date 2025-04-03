from datetime import datetime, timedelta
from time import perf_counter_ns
from functools import wraps
from .client import IFClient, Node

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
    "MD-11": "MD11",
    "E175": "E175",
    "DC-10F": "DC10F",
}



from typing import Callable

class IFProperty:
    def __init__(self, command: str, get_custom_func: Callable = None, set_custom_func: Callable = None):
        self.command = command
        self.get_custom_func = get_custom_func
        self.set_custom_func = set_custom_func

    def __set_name__(self, owner, name):
        self._name = "_" + name

    def __get__(self, instance, owner):
        if instance is None:
            return self
        
        if self.get_custom_func is not None:
            return self.get_custom_func(self.command)
        return self.command

    def __set__(self, instance, value):
        if self.set_custom_func is not None:
            value = self.set_custom_func(value)
        print(value)


# def attrs_to_property(cls):
#     attrs = dir(cls)
#     filter_attrs = filter(lambda x: not x.startswith("__") and not callable(getattr(cls, x)), attrs)
#     client_attr: IFClient = next(filter(lambda attr: isinstance(IFClient, attr), filter_attrs))
#     filter_attrs = filter(lambda x: not x.startswith("__") and not callable(getattr(cls, x)), attrs)
#     manifest_attr: Node = next(filter(lambda attr: isinstance(Node, attr), filter_attrs), None)

#     if client_attr is None:
#         raise AttributeError(f"No {"IFClient":!r} attr found")

#     for attrs_name, value in cls.__dict__.items():
#         if not attrs_name.startswith("__") and not callable(value):
#             def getter(self, cmd=value):
#                 if manifest_attr is not None:
#                     bin_cmd: tuple[int, int] = manifest_attr.search(cmd[:-1])            
#                 else:
#                     manifest: Node = next(filter(lambda _, v: isinstance(v, Node), globals().items()))
#                     if manifest is None:
#                         raise AttributeError(f"No {"Node":!r} attr found")
#                     bin_cmd = manifest.search(cmd[:-1])
#                 tmp = client_attr.send_command(*bin_cmd)
#                 return tmp * cmd[-1]

#             def setter(self, val, cmd=value):
#                 if manifest_attr is not None:
#                     bin_cmd: tuple[int, int] = manifest_attr.search(cmd)            
#                 else:
#                     manifest: Node = next(filter(lambda _, v: isinstance(v, Node), globals().items()))
#                     if manifest is None:
#                         raise AttributeError(f"No {"Node":!r} attr found")
#                     bin_cmd = manifest.search(cmd)
#                 client_attr.send_command(*bin_cmd, val)*cmd[-1]
#             setattr(cls, attrs_name, property(getter, setter))

#     return cls