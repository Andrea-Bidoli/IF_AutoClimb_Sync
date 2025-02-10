from module import IFFPL, Fix, dist_to_fix, FlightPhase
from module import Aircraft, Autopilot, Autothrottle
from module import logger, debug_logger

from .convertion import PintUnitManager, Quantity
from numpy import arctan2, sin, sign, radians
from numpy import cos, arccos, sqrt, arcsin
# from datetime import datetime, timedelta
from time import sleep
from math import isclose

from enum import Enum, auto


dummy_fix = Fix("None", -1, -1, -1, -1)
unit: PintUnitManager = PintUnitManager()
class Spd(Enum):
    clb_V1 = auto()
    clb_V2 = auto()
    clb_V3 = auto()
    Vr = auto()
    crz_V = auto()
    

def takeoff(aircraft: Aircraft, autopilot: Autopilot, inputs: dict[str, str]) -> None:
    if not aircraft.is_on_ground:
        return
    logger.info("Starting takeoff")
    k = None
    TO_setting: float = 0
    flex_temp: str = input("FLEX temperature : ") or ""
    # flap_spd: str = input("Flap retract speed : ") or ""
    match flex_temp.split('-'):
        case (dto, temp):
            dto = int(dto)
            temp = int(temp)
        case (temp,):
            dto = 0
            temp = int(temp)
    try:
        k = aircraft.airplane.k
        if temp >= aircraft.OAT:
            TO_setting = ((100-dto*10) - k * (temp - aircraft.OAT)) / 100
    except AttributeError: ...
    except TypeError: ...

    if inputs.get("Vr"):
        autopilot.Spd = (int(inputs["Vr"])*unit.knot).to(unit.ms).magnitude

    if temp > 2 and TO_setting == 0:
        logger.warning("Aircraft don't support FLEX TEMP, please take off manually")
        return
    elif temp <= 2 and TO_setting == 0:
        TO_setting = (100 - temp * 10) / 100

    logger.info(f"Flex temp: {dto}-{temp} TO setting: {TO_setting: .2f}")
    while aircraft.n1 < 0.5 or (not aircraft.is_on_runway and aircraft.is_on_ground):
        sleep(1)
    autopilot.Throttle = TO_setting
    logger.info(f"Starting takeoff\nTO n1:{aircraft.n1_target:.2f}")
    while aircraft.is_on_ground or (aircraft.agl < 50 and aircraft.vs < 0): 
        sleep(1)
    debug_logger.debug("Takeoff")
    if aircraft.landing_gear_status:
        debug_logger.debug("Landing gear is up")
        return
    debug_logger.debug("Landing gear is down, trying to retract")
    aircraft.Landing_gear_toggle

class Vnav:
    def __init__(self, aircraft: Aircraft, autopilot: Autopilot, fpl: IFFPL, inputs: dict[str, str]):
        if fpl is None:
            logger.warning("No flight plan found, unable to perform VNAV")
            return

        self.above_10k = False

        self.aircraft = aircraft
        self.autopilot = autopilot
        self.fpl = fpl
        self.inputs = inputs
        self.vnav_wps = fpl.vnav_wps()
        self.autothrottle = Autothrottle(self.aircraft, self.autopilot)
        self.check_inputs()

    def check_inputs(self):
        if v := self.inputs.get(Spd.clb_V1):
            self.aircraft.airplane.climb_v1 = (int(v)*unit.knot).to(unit.ms).magnitude        
        if v := self.inputs.get(Spd.clb_V2):
            self.aircraft.airplane.climb_v2 = (int(v)*unit.knot).to(unit.ms).magnitude
        if v := self.inputs.get(Spd.clb_V3):
            self.aircraft.airplane.climb_v3 = (int(v)*unit.knot).to(unit.ms).magnitude
        if v := self.inputs.get(Spd.crz_V):
            self.aircraft.airplane.cruise_speed = float(v)

    def set_speed(self, target_speed: Quantity) -> None:
        """Set the target speed and update both autopilot and autothrottle."""
        self.autothrottle.set_target_speed(target_speed)
        logger.info(f"Speed set to {target_speed.to(unit.knot):.0f} knots")
    
    def __call__(self) -> None:
        # TODO: define `waipoint`
        descent_angle = radians(3)
        time_target = 2 * 60

        if self.aircraft.next_index > waypoint.index:
            waypoint = next(self.vnav_wps, dummy_fix)
            return
        
        match waypoint.flight_phase:
            case FlightPhase.CLIMB:
                self.handle_climb(waypoint)
            case FlightPhase.CRUISE:
                self.handle_cruise(waypoint, time_target)
            case FlightPhase.DESCENT:
                return
                self.handle_descent(waypoint, descent_angle)
        
        sleep(1)

    def handle_climb(self, waypoint: Fix):
        self.autothrottle(waypoint)

        if not self.above_10k and self.aircraft.msl >= (10_000*unit.ft).to(unit.m).magnitude:
            if self.aircraft.landing_lights_status:
                self.aircraft.Landing_Lights_toggle
            if self.aircraft.seat_belt_status:
                self.aircraft.seat_belt_toggle
            self.above_10k = True

        delta_alt = waypoint.alt - self.aircraft.msl
        dist = dist_to_fix(waypoint, self.fpl, self.aircraft)
        vs_sin = delta_alt / (dist**2 + delta_alt**2)**.5
        self.autopilot.Vs = self.aircraft.gs * vs_sin

    def handle_cruise(self, waypoint: Fix, time_target: float):
        delta_alt = waypoint.alt - self.autopilot.Alt
        target_vs = sign(delta_alt) * max((200*unit.ft).to(unit.m), min((1000*unit.ft).to(unit.m).magnitude, abs(delta_alt / time_target)))
        climb_time = delta_alt / target_vs
        ete_fix = dist_to_fix(waypoint, self.fpl, self.aircraft) / self.aircraft.gs - climb_time
        
        if not isclose(self.autopilot.Spd, self.aircraft.airplane.cruise_speed, abs_tol=1e-4):
            self.autothrottle.set_target_speed(self.aircraft.airplane.cruise_speed)
        self.autothrottle(waypoint)
        if ete_fix <= 0:
            self.autopilot.Alt = waypoint.alt
            self.autopilot.Vs = target_vs
            self.vnav_wps = self.fpl.update_vnav_wps(self.aircraft)
        elif ete_fix > 6 * 60:
            sleep(5 * 60)
        else:
            sleep(10)

    def handle_descent(self, waypoint: Fix, sin_angle: float):
        # TODO: implement descent
        delta_alt = waypoint.alt - self.autopilot.Alt
        dist = dist_to_fix(waypoint, self.fpl, self.aircraft)
        vs_sin = delta_alt / (dist**2 + delta_alt**2)**.5
        target_vs = self.aircraft.gs * vs_sin
        
        if not isclose(self.autopilot.Alt, waypoint.alt, abs_tol=1e-4):
            self.autopilot.Alt = waypoint.alt
        self.autopilot.Vs = min(sin_angle, target_vs)

class Lnav:
    def __init__(self, aircraft: Aircraft, autopilot: Autopilot, fpl: IFFPL):
        self.aircraft = aircraft
        self.autopilot = autopilot
        self.fpl = fpl
        self.target_bank = radians(30)
        self.next_index = self.aircraft.next_index
    
    def create_holding(self, fix: Fix, lenght: Quantity, direction: Quantity, width: float, side: str = 'left'):
        def create_fix(fix: Fix, dist: Quantity, direction_: Quantity, index: int):
            lat2 = fix.lat + (dist.to(unit.nm)/60)*cos(direction_.to(unit.rad))
            lon2 = fix.lon + (dist.to(unit.nm)/60)*sin(direction_.to(unit.rad)) / cos(lat2)
            return Fix("Holding-1", -1, lat2, lon2, index)
        directions = [90, 180, 270]
        match side.lower():
            case 'left'|'l':
                directions = map(lambda x: x*-1, directions)
            case 'right'|'r':
                direction = (i for i in directions)
        fixes = [fix]
        for i, direction_ in enumerate(directions):
            fixes.append(create_fix(fixes[-1], lenght if i % 2 == 0 else width, direction + direction_*unit.deg, i+1))
        return fixes

    def execute_holding(self, holding: tuple[Fix, Fix, Fix, Fix]):
        ...

    @staticmethod
    def get_track_angle(fix1: Fix, fix2: Fix) -> Quantity:
        lat1, lon1, lat2, lon2 = fix1.lat, fix1.lon, fix2.lat, fix2.lon
        dlon = lon2 - lon1
        x = sin(dlon) * cos(lat2)
        y = cos(lat1) * sin(lat2) - sin(lat1) * cos(lat2) * cos(dlon)
        return arctan2(x, y)*unit.rad


    def __call__(self):
        true_track = self.get_track_angle(self.fpl[self.next_index], self.fpl[self.next_index+1])
        variation = self.aircraft.send_command("magnetic_variation")
        mag_track = true_track + variation
        self.autopilot.Hdg += mag_track - self.autopilot.Hdg
        

def Only_Authothrottle(aircraft: Aircraft, autopilot: Autopilot, inputs: dict[str, str]):
    logger.info("Starting autothrottle")
    while aircraft.is_on_ground:
        sleep(1)
    autothrottle = Autothrottle(aircraft, autopilot)
    fix = Fix("None", -1, -1, -1, -1)
    fix._flight_phase = FlightPhase.CLIMB
    while aircraft.msl < autopilot.Alt:
        if aircraft.msl >= (10_000*unit.ft).to(unit.m) and aircraft.landing_lights_status:
            if aircraft.landing_lights_status:
                aircraft.Landing_Lights_toggle
            if aircraft.seat_belt_status:
                aircraft.seat_belt_toggle

        autothrottle(fix)
        sleep(1)
    