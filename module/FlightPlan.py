from numpy import arccos, arctan2, cos, arcsin, sin, cross, array, pi
from .convertion import decimal_to_dms
from .logger import logger
from . import unit, Quantity
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
    TAKE_OFF = auto()
    CLIMB = auto()
    CRUISE = auto()
    DESCENT = auto()
    NULL = auto()

# TODO: rewrite all IFFPL to accept self instances

type dataType = str | dict | TextIOWrapper | list
type jsonType = str | dict | TextIOWrapper

@dataclass(slots=True)
class Fix:
    name: str
    alt: Quantity
    lat: Quantity
    lon: Quantity
    _index: int
    dist_to_next: Quantity = field(init=False, default=0)
    _flight_phase: int = field(init=False, default=FlightPhase.NULL)

    def __post_init__(self):
        self.lat = (self.lat * unit.deg).to(unit.rad)
        self.lon = (self.lon * unit.deg).to(unit.rad)
        self.alt = (self.alt * unit.ft).to(unit.m)
        self.dist_to_next *= unit.m

    def __str__(self):
        return  f"name={self.name} alt={(self.alt.to(unit.ft))}\n"+\
                f"lat={decimal_to_dms(self.lat.to(unit.deg).magnitude)} lon={decimal_to_dms(self.lon.to(unit.deg).magnitude)}\n"+\
                f"index={self._index} dist={self.dist_to_next}\n"+\
                f"flight phase={self.flight_phase}"

    def __format__(self, format_spec: str) -> str:
        def matching(i: tuple[str, str]):
            if i[-1]:
                attr = getattr(self, i[0].replace(i[-1], ""))
                if attr is None:
                    return f"{attr}"
                return f"{attr:{i[-1]}}"
            return f"{getattr(self, i[0])}"

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
    
    @classmethod
    def from_str(cls, flight_plan_data: str | dict, write: bool = False) -> 'IFFPL':
        cls._allow_creation = True
        try:
            if isinstance(flight_plan_data, str):
                file_decoded = loads(flight_plan_data)
            else:
                detailFPL = flight_plan_data
            detailFPL = file_decoded["detailedInfo"]["flightPlanItems"]
        except (TypeError, KeyError):
            detailFPL = False
        if not detailFPL:
            logger.warning("No flight plan defined")
            return None

        if write:
            with open("logs/fpl.json", "w") as f:
                dump(file_decoded, f, indent=4)

        return cls(detailFPL)
    
    @classmethod
    def from_list(cls, flight_plan_data: list, write: bool = False) -> "IFFPL":
        cls._allow_creation = True
        if not all(isinstance(i, Fix) for i in flight_plan_data):
            raise ValueError("non valid data type")
        if write:
            logger.warning("Not able to write list to file")
        return cls(flight_plan_data)

    @classmethod
    def from_file(cls, file: TextIOWrapper, write: bool = False) -> "IFFPL":
        cls._allow_creation = True
        try:
            fpl_tmp = load(file)['detailedInfo']['flightPlanItems']
        except (TypeError, KeyError):
            logger.warning("No flight plan defined")
            return None
        if write: ...
        return cls(fpl_tmp)

    def __new__(cls, *args, **kwargs) -> "IFFPL":
        if not hasattr(cls, "_allow_creation") or not cls._allow_creation:
            raise TypeError("IFFPL can't be initialized directly")
        cls._allow_creation = False
        return super().__new__(cls)

    def __init__(self, data: list[Fix | dict[str,]]) -> "IFFPL":
        if all(isinstance(i, dict) for i in data):
            self.json_init(data)         
        else:
            self.from_list(data)

    def set_list(self, json_list: list) -> None:
        for obj in json_list:
            if obj["children"] is not None:
                self.set_list(obj["children"])
                continue
            name = obj["identifier"] if obj["name"] == None else obj["name"]
            alt = obj["location"]["AltitudeLight"] if obj["location"]["AltitudeLight"] != 0 else obj["altitude"]
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

    def json_init(
        self, data) -> None:
        self.good_fpl = True
        self.TOC_finded = False
        self.TOD_finded = False
        self._index = 0

        
        self.set_list(data)
                
        if next(filter(lambda x: x.name.lower() == "toc", self), None) is None:
            self.good_fpl = False

        self.post_init()
    
    def post_init(self):
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
            # TODO: check if it works properly
            copy = sorted(copy, key=lambda x: (x.alt, x.index), reverse=True)
            tmp: set[Fix] = set()
            tmp.add(copy[0])
            for fix1, fix2 in pairwise(copy):
                if fix2.alt - fix1.alt <= 2000*unit.ft:
                # if isclose(fix1.alt - fix2.alt, 2000*unit.ft, abs_tol=1e-9, rel_tol=1e-9):
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
                cruise_finish = max(self[tmp_list[-1].index+1:], key=lambda x: x.alt).index

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

    def update_vnav_wps(self, aircraft: 'Aircraft') -> Generator[Fix, None, None]:
        self.__init__(aircraft.client.send_command("full_info"))
        return self.vnav_wps(aircraft.next_index)

    def extend_from_index(self, data: list[Fix], index: int) -> None:
        self[index:index] = data


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

def get_point(start_fix: Fix, dist: Quantity, bearing: Quantity) -> Fix:
    d_D = dist.to(unit.m)/6371e3
    cos_bearing = cos(bearing.to(unit.rad))
    sin_bearing = sin(bearing.to(unit.rad))
    cos_d_D = cos(d_D)
    sin_d_D = sin(d_D)
    
    lat_2 = arcsin(sin(start_fix.lat) * cos_d_D + cos(start_fix.lat) * sin_d_D * cos_bearing)
    lon_2 = start_fix.lon + arctan2(sin_bearing * sin_d_D * cos(start_fix.lat), cos_d_D - sin(start_fix.lat) * sin(lat_2))
    return Fix("Point", -1*unit.ft, lat_2*unit.rad, lon_2*unit.rad, -1)
    
def cosine_law(fix1: Fix, fix2: Fix) -> Quantity:
    phi_1 = fix1.lat
    phi_2 = fix2.lat
    delta_lambda = fix2.lon - fix1.lon
    R = 6371e3
    return (
        arccos(sin(phi_1) * sin(phi_2) + cos(phi_1) * cos(phi_2) * cos(delta_lambda))
        * R
    ).m*unit.m

def dist_fix_fix(fix1: Fix, fix2: Fix, fpl: IFFPL) -> Quantity:
    if fix1.index > fix2.index:
        fix1, fix2 = fix2, fix1
    
    start = fix1.index
    end = fix2.index
    
    l = map(lambda x: x.dist_to_next, fpl[start:end])
    
    return sum(l)

def dist_to_fix(fix: Fix, fpl: IFFPL, aircraft: 'Aircraft') -> Quantity:
    if fix.index == aircraft.next_index:
        return aircraft.dist_to_next
    else:
        fix_1 = next(filter(lambda x: x.index == aircraft.next_index, fpl))
        return dist_fix_fix(fix_1, fix, fpl) + aircraft.dist_to_next
