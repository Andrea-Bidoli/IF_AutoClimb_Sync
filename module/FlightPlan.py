from dataclasses import dataclass, field
from itertools import pairwise

from numpy import arccos, arctan2, cos, degrees, radians, sin
from .aircraft import Aircraft
from json import loads, dump

@dataclass(slots=True)
class Fix:
    name: str
    altitude: int
    latitude: float
    longitude: float
    _index: int
    dist_to_next: float = field(init=False, default=0)
    angle: float = field(init=False, default=0)

    def __post_init__(self):
        self.latitude = radians(self.latitude)
        self.longitude = radians(self.longitude)

    def __repr__(self):
        return f"name={self.name} alt={self.altitude}\nlat={self.latitude} lon={self.longitude}\nindex={self._index} dist={self.dist_to_next}\nalpha={degrees(self.angle)}"
    @property
    def index(self) -> int:
        return self._index

class IFFPL(list[Fix]):
    def __new__(cls, json_data: str|dict, write: bool=False) -> "IFFPL":
        if isinstance(json_data, (str, bytearray, bytes)):
            json_data: dict = loads(json_data)
        elif not isinstance(json_data, dict):
            raise ValueError("json_data must be a string or a dictionary")
        if json_data["detailedInfo"] is None:
            print("No flight plan defined")
            return None
        
        instance = super().__new__(cls)
        return instance
    
    def __init__(self, json_data: str|dict|None=None, write: bool=False) -> None:
        super().__init__()
        if isinstance(json_data, str):
            json_data = loads(json_data)
        if write:
            with open("logs/fpl.json", "w") as f:
                dump(json_data, f, indent=4)
        for key, value in json_data["detailedInfo"].items():
            if key == "flightPlanItems":
                index = 0
                for obj in value:
                    if obj["children"] is not None:
                        for child in obj["children"]:
                            name = child["identifier"] if child["name"] == None else child["name"]
                            alt = child["altitude"]*0.3048 if child["altitude"]>0 else 0
                            tmp = Fix(name, alt, child["location"]["Latitude"], child["location"]["Longitude"], index)
                            self.append(tmp)
                            index += 1
                    else:
                        name = obj["identifier"] if obj["name"] == None else obj["name"]
                        alt = obj["altitude"]*0.3048 if obj["altitude"]>0 else 0
                        tmp = Fix(name, alt, obj["location"]["Latitude"], obj["location"]["Longitude"], index)
                        self.append(tmp)
                        index += 1
        self.__post_init__()

    def __post_init__(self):
        for fix_1, fix_2 in pairwise(self):
            if fix_2.altitude <= 0 and fix_1.altitude > 0:
                fix_2.altitude = fix_1.altitude
            fix_1.dist_to_next = cosine_law(fix_1, fix_2)
            fix_1.angle = arctan2(fix_2.altitude - fix_1.altitude, fix_1.dist_to_next)

    def shift(n: int) -> None:
        n = n % len(self)
        self = self[n:] + self[:n]

def get_bearing(fix1: Fix, fix2: Fix) -> float:
    d_lon = fix2.longitude - fix1.longitude
    x = sin(d_lon) * cos(fix2.latitude)
    y = cos(fix1.latitude) * sin(fix2.latitude) - sin(fix1.latitude) * cos(fix2.latitude) * cos(d_lon)
    return arctan2(x, y)

def cosine_law(fix1: Fix, fix2: Fix) -> float:
    phi_1 = fix1.latitude
    phi_2 = fix2.latitude
    delta_lambda = fix2.longitude - fix1.longitude
    R = 6371e3
    return arccos(sin(phi_1) * sin(phi_2) + cos(phi_1) * cos(phi_2) * cos(delta_lambda)) * R

def dist_fix_fix(start_fix: Fix, end_fix: Fix, waypoint_route: list[Fix]) -> float:
    total_distance = 0.0
    start, finish = waypoint_route.index(start_fix), waypoint_route.index(end_fix)+1
    for fix1, fix2 in pairwise(waypoint_route[start:finish]):
        total_distance += cosine_law(fix1=fix1, fix2=fix2)
    return total_distance

def dist_to_fix(fix: Fix, fpl: IFFPL, aircraft: Aircraft) -> float:
    if fpl.index(fix) == aircraft.next_index:
        return aircraft.dist_to_next
    else:
        return dist_fix_fix(fpl[aircraft.next_index], fix, fpl) + aircraft.dist_to_next