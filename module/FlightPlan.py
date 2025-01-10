from numpy import arccos, arctan2, cos, degrees, radians, sin, cross, array, pi
from .convertion import m2ft, ft2m, decimal_to_dms
from .logger import logger
from dataclasses import dataclass, field
from itertools import pairwise
from collections.abc import Generator
from json import loads, load, dump
from numpy.linalg import norm
from io import TextIOWrapper
from re import findall

from enum import Enum, auto

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .aircraft import Aircraft

class FlightPhase(Enum):
    CLIMB = auto()
    CRUISE = auto()
    DESCENT = auto()
    NULL = auto()



@dataclass(slots=True)
class Fix:
    name: str
    alt: int
    lat: float
    lon: float
    _index: int
    dist_to_next: float = field(init=False, default=0)
    _flight_phase: int = field(init=False, default=FlightPhase.NULL)

    def __post_init__(self):
        self.lat = radians(self.lat)
        self.lon = radians(self.lon)

    def __str__(self):
        return  f"name={self.name} alt={m2ft(self.alt)}\n"+\
                f"lat={decimal_to_dms(degrees(self.lat))} lon={decimal_to_dms(degrees(self.lon))}\n"+\
                f"index={self._index} dist={self.dist_to_next}\n"+\
                f"flight phase={self.flight_phase}"

    def __format__(self, format_spec: str) -> str:
        def matching(i: tuple[str, str]):
            if i[-1]:
                attr = (
                    getattr(self, i[0].replace(i[-1], ""))
                    if i[0] != "angle"
                    else degrees(getattr(self, i[0]))
                )
                if attr is None:
                    return f"{attr}"
                return f"{attr:{i[-1]}}"
            return f"{getattr(self, i[0]) if i[0] != 'angle' else degrees(getattr(self, i[0]))}"

        list_of_format = findall(r"%([a-zA-Z]+(\.[a-zA-Z0-9]+)?)", format_spec)

        return "\n".join(map(matching, list_of_format))

    def __hash__(self):
        return hash((self.name, self.index))

    @property
    def index(self) -> int:
        return self._index

    @property
    def flight_phase(self) -> int:
        return self._flight_phase

class IFFPL(list[Fix]):
    def __new__(cls, json_data: str | dict, write: bool = False) -> "IFFPL":
        if not isinstance(json_data, (str, bytearray, bytes, dict, TextIOWrapper)):
            raise ValueError("json_data must be a string or a dictionary")
        if isinstance(json_data, TextIOWrapper):
            detailFPL = load(json_data)["detailedInfo"]
            json_data.seek(0, 0)
        else:
            try:
                detailFPL = loads(json_data)["detailedInfo"]["flightPlanItems"]
            except TypeError:
                detailFPL = False
        if not detailFPL:
            logger.warning("No flight plan defined")
            return None

        instance = super().__new__(cls)
        return instance

    def set_list(self, json_list: list) -> None:
        for obj in json_list:
            if obj["children"] is not None:
                self.set_list(obj["children"])
                continue
            name = obj["identifier"] if obj["name"] == None else obj["name"]
            alt = ft2m(obj["location"]["AltitudeLight"]) if obj["location"]["AltitudeLight"] != 0 else ft2m(obj["altitude"])
            self.append(
                Fix(
                    name,
                    alt,
                    obj["location"]["Latitude"],
                    obj["location"]["Longitude"],
                    self._index
                )
            )
            self._index += 1

    def __init__(
        self, json_data: str | dict | TextIOWrapper | None = None, write: bool = False
    ) -> None:
        super().__init__()
        self.good_fpl = True
        self.TOC_finded = False
        self.TOD_finded = False
        if isinstance(json_data, TextIOWrapper):
            self.json_data = load(json_data)
        else:
            self.json_data = loads(json_data) if isinstance(json_data, (str, bytes, bytearray)) else json_data
        self._index = 0
        
        def filter_func(x):
            if x["name"] is None:
                return False
            return x["name"].lower() != "toc"
        
        if next(filter(filter_func, 
                       self.json_data["detailedInfo"]["flightPlanItems"]), None) is None:
            self.good_fpl = False
        
        if write:
            with open("logs/fpl.json", "w") as f:
                dump(self.json_data, f, indent=4)
        
        for key in self.json_data["detailedInfo"]:
            if key == "flightPlanItems":
                self.set_list(self.json_data["detailedInfo"]["flightPlanItems"])
        
        self.__post_init__()
    
    def __post_init__(self):
        if self.good_fpl:
            for fix in self:
                if self.TOC_finded and self.TOD_finded:
                    fix._flight_phase = FlightPhase.DESCENT

                elif self.TOC_finded and not self.TOD_finded:
                    if fix.name.lower() == "tod":
                        self.TOD_finded = True
                        fix._flight_phase = FlightPhase.DESCENT
                        continue
                    fix._flight_phase = FlightPhase.CRUISE

                elif not self.TOC_finded and not self.TOD_finded:
                    fix._flight_phase = FlightPhase.CLIMB
                    if fix.name.lower() == "toc":
                        self.TOC_finded = True

        else:
            copy = [fix for fix in self if fix.alt > 0]
            copy = sorted(copy, key=lambda x: x.alt, reverse=True)
            tmp: set[Fix] = set()
            tmp.add(copy[0])
            for fix1, fix2 in pairwise(copy):
                if abs(fix1.alt - fix2.alt) <= ft2m(2000):
                    tmp.add(fix1)
                    tmp.add(fix2)

                else: break

            tmp_list = list(tmp)
            
            if len(tmp_list) == 1:
                cruise_start = tmp_list[0].index + 1
                cruise_finish = max(self[cruise_start:], key=lambda x: x.alt).index

            else:
                tmp_list.sort(key=lambda x: x.index)
                cruise_start = tmp_list[0].index
                cruise_finish = max(self[tmp_list[-1].index:], key=lambda x: x.alt).index


            for fix in self:
                if fix.index < cruise_start:
                    fix._flight_phase = FlightPhase.CLIMB
                elif cruise_start <= fix.index < cruise_finish:
                    fix._flight_phase = FlightPhase.CRUISE
                else:
                    fix._flight_phase = FlightPhase.DESCENT

        for fix_1, fix_2 in pairwise(self):
            fix_1.dist_to_next = cosine_law(fix_1, fix_2)


    def vnav_wps(self, start: int = 0) -> Generator[Fix, None, None]:
        yield from filter(lambda x: x.alt > 0, self[start:])

    def update_vnav_wps(self, client: 'Aircraft') -> Generator[Fix, None, None]:
        self.__init__(client.send_command("full_info"))
        return self.vnav_wps(client.next_index)


def angle_between_3_fix(fix1: Fix, fix2: Fix, fix3: Fix):
    p1 = array(
        [
            cos(fix1.lat) * cos(fix1.lon),
            cos(fix1.lat) * sin(fix1.lon),
            sin(fix1.lat),
        ]
    )

    p2 = array(
        [
            cos(fix2.lat) * cos(fix2.lon),
            cos(fix2.lat) * sin(fix2.lon),
            sin(fix2.lat),
        ]
    )

    p3 = array(
        [
            cos(fix3.lat) * cos(fix3.lon),
            cos(fix3.lat) * sin(fix3.lon),
            sin(fix3.lat),
        ]
    )

    n1 = cross(p1, p2)
    n2 = cross(p3, p2)

    n1 = n1 / norm(n1)
    n2 = n2 / norm(n2)

    theta = arccos(n1 @ n2)
    return min(pi - theta, theta)


def get_bearing(fix1: Fix, fix2: Fix) -> float:
    delta_lon = fix2.lon - fix1.lon
    X = cos(fix2.lat) * sin(delta_lon)
    Y = cos(fix1.lat) * sin(fix2.lat) - sin(fix1.lat) * cos(fix2.lat) * cos(delta_lon)
    return arctan2(X, Y)


def cosine_law(fix1: Fix, fix2: Fix) -> float:
    phi_1 = fix1.lat
    phi_2 = fix2.lat
    delta_lambda = fix2.lon - fix1.lon
    R = 6371e3
    return (
        arccos(sin(phi_1) * sin(phi_2) + cos(phi_1) * cos(phi_2) * cos(delta_lambda))
        * R
    )

def dist_fix_fix(fix1: Fix, fix2: Fix, fpl: IFFPL) -> float:
    if fix1.index > fix2.index:
        fix1, fix2 = fix2, fix1
    
    start = fix1.index
    end = fix2.index
    
    l = map(lambda x: x.dist_to_next, fpl[start:end])
    
    return sum(l)

def dist_to_fix(fix: Fix, fpl: IFFPL, aircraft: 'Aircraft') -> float:
    if fix.index == aircraft.next_index:
        return aircraft.dist_to_next
    else:
        fix_1 = next(filter(lambda x: x.index == aircraft.next_index, fpl))
        return dist_fix_fix(fix_1, fix, fpl) + aircraft.dist_to_next
