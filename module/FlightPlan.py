from numpy import arccos, arctan2, cos, degrees, radians, sin, cross, array, pi
from dataclasses import dataclass, field
from itertools import pairwise, islice
from collections.abc import Generator
from numpy.linalg import norm
from collections import deque
from json import loads, dump
from .convertion import m2ft
from re import findall

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .aircraft import Aircraft


@dataclass(slots=True)
class Fix:
    name: str
    alt: int
    lat: float
    lon: float
    _index: int
    dist_to_prev: float = field(init=False, default=0)
    angle: float = field(init=False, default=None)

    def __post_init__(self):
        self.lat = radians(self.lat)
        self.lon = radians(self.lon)

    def __repr__(self):
        return f"name={self.name} alt={m2ft(self.alt)}\nlat={self.lat} lon={self.lon}\nindex={self._index} dist={self.dist_to_prev}\nalpha={degrees(self.angle)if self.angle is not None else None}"

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

    @property
    def index(self) -> int:
        return self._index


class IFFPL(deque[Fix]):
    def __new__(cls, json_data: str | dict, write: bool = False) -> "IFFPL":
        if isinstance(json_data, (str, bytearray, bytes)):
            json_data: dict = loads(json_data)
        elif not isinstance(json_data, dict):
            raise ValueError("json_data must be a string or a dictionary")
        if json_data["detailedInfo"] is None:
            print("No flight plan defined")
            return None

        instance = super().__new__(cls)
        instance.json_data = json_data
        return instance

    def __init__(
        self, json_data: str | dict | None = None, write: bool = False
    ) -> None:
        super().__init__()
        self._index = 0
        if write:
            with open("logs/fpl.json", "w") as f:
                dump(self.json_data, f, indent=4)
        for key, value in self.json_data["detailedInfo"].items():
            if key == "flightPlanItems":
                index = 0
                for obj in value:
                    if obj["children"] is not None:
                        for child in obj["children"]:
                            name = (
                                child["identifier"]
                                if child["name"] is None
                                else child["name"]
                            )
                            alt = (
                                max(
                                    child["altitude"],
                                    child["location"]["AltitudeLight"],
                                )
                                * 0.3048
                            )
                            tmp = Fix(
                                name,
                                alt,
                                child["location"]["Latitude"],
                                child["location"]["Longitude"],
                                index,
                            )
                            self.append(tmp)
                            index += 1
                    else:
                        name = obj["identifier"] if obj["name"] == None else obj["name"]
                        alt = alt = (
                            max(obj["altitude"], obj["location"]["AltitudeLight"])
                            * 0.3048
                        )
                        tmp = Fix(
                            name,
                            alt,
                            obj["location"]["Latitude"],
                            obj["location"]["Longitude"],
                            index,
                        )
                        self.append(tmp)
                        index += 1
        self.post_init()
        n = self.json_data["nextWaypointIndex"]
        self.rotate(n)

    def post_init(self):
        for fix_1, fix_2 in pairwise(self):
            fix_2.dist_to_prev = cosine_law(fix_1, fix_2)

        fixs = filter(lambda x: x.alt > 0, list(self))
        for fix_1, fix_2 in pairwise(fixs):
            fix_2.angle = arctan2(
                fix_2.alt - fix_1.alt, dist_fix_fix(fix_1, fix_2, self)
            )

    def find_stepclimb_wps(self) -> Generator[Fix, None, None]:
        tmp = filter(lambda x: x.alt > 0 and x.angle is not None, self)
        yield from tmp

    def find_climb_wps(self) -> Generator[Fix, None, None]:
        toc = next(filter(lambda x: x.name.lower() == "toc", self), None)
        if toc is None:
            return
        yield from islice(self, toc.index + 1)

    def find_descent_wps(self) -> Generator[Fix, None, None]:
        tod = next(filter(lambda x: x.name.lower() == "tod", self))
        if tod is None:
            return
        yield from islice(self, tod.index, len(self))


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


def dist_fix_fix(start_fix: Fix, end_fix: Fix, waypoint_route: IFFPL[Fix]) -> float:
    total_distance = 0.0
    # waypoint_route.reset_index()
    start, finish = waypoint_route.index(start_fix), waypoint_route.index(end_fix) + 1
    for fix in islice(waypoint_route, start, finish):  # waypoint_route[start:finish]
        total_distance += fix.dist_to_prev
    return total_distance


def dist_to_fix(fix: Fix, fpl: IFFPL, aircraft: "Aircraft") -> float:
    if fpl.index(fix) == aircraft.next_index:
        return aircraft.dist_to_next
    else:
        return dist_fix_fix(fpl[aircraft.next_index], fix, fpl) + aircraft.dist_to_next
