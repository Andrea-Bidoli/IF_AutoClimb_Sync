from .FlightPlan import IFFPL, Fix, dist_to_fix, FlightPhase, cosine_law
from .aircraft import Aircraft, Autopilot, Autothrottle, Spd
from .logger import logger, debug_logger
from .utils import format_time

from . import unit, Quantity
from numpy import arctan2, sin, sign, radians, cos, arcsin
from datetime import datetime, timedelta
from time import sleep
from math import isclose


dummy_fix = Fix("None", -1, -1, -1, -1)
dummy_fix._flight_phase = FlightPhase.NULL
    

def takeoff(aircraft: Aircraft, autopilot: Autopilot, autothrottle: Autothrottle, inputs: dict[str, str]) -> None:
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

    if temp > 2 and TO_setting == 0:
        logger.warning("Aircraft don't support FLEX TEMP, please take off manually")
        return
    elif temp <= 2 and TO_setting == 0:
        TO_setting = (100 - temp * 10) / 100

    logger.info(f"Flex temp: {dto}-{temp} TO setting: {TO_setting: .2f}")
    
    if (v := inputs.get(Spd.Vr)) is not None:
        autopilot.Spd = v
    # //
    while aircraft.n1 < 0.5*unit.no_unit or (not aircraft.is_on_runway and aircraft.is_on_ground):
        sleep(1)
    autothrottle.Throttle = TO_setting
    logger.info(f"Starting takeoff\nTO n1:{aircraft.n1_target:.2f}")
    while aircraft.is_on_ground or (aircraft.agl < 50*unit.ft and aircraft.vs < 0*unit.fpm): 
        sleep(1)
    debug_logger.debug("Takeoff")
    if not aircraft.landing_gear_status:
        debug_logger.debug("Landing gear is up")
        return
    debug_logger.debug("Landing gear is down, trying to retract")
    aircraft.Landing_gear_toggle

class Vnav:
    descent_angle = 3*unit.deg
    time_target = 2 * 60 * unit.s

    def __init__(self, aircraft: Aircraft, autopilot: Autopilot, autothrottle: Autothrottle, fpl: IFFPL):
        logger.info("Initializing VNAV...")
        
        if fpl is None:
            logger.warning("No flight plan found, unable to perform VNAV")
            return

        self.above_10k = False
        self.aircraft = aircraft
        self.autopilot = autopilot
        self.fpl = fpl
        self.vnav_wps = fpl.vnav_wps()
        self.waypoint = next(self.vnav_wps, dummy_fix)
        self.autothrottle = autothrottle
        
        logger.info("VNAV initialized!")

    def set_target_speed(self, target_speed: Quantity) -> None:
        """Set the target speed and update both autopilot and autothrottle."""
        self.autothrottle.target_spd = target_speed
        
        if target_speed.magnitude > 1:
            spd = target_speed.to(unit.knot)
        else:
            spd = target_speed.to(unit.mach)
        # FIXME: check if the speed is already set to the target speed and check compatibility with unit
        if spd.units != unit.mach and (self.autopilot.Spd.m_as(unit.knot) != target_speed.m_as(unit.knot)):
            logger.info(f"Speed set to {spd: 5.2f}")
        else:
            logger.info(f"Mach set to {spd.m: .2f}")

    def __call__(self) -> None:
        if self.aircraft.next_index > self.waypoint.index:
            self.waypoint = next(self.vnav_wps, dummy_fix)
            return False
        if not self.aircraft.is_on_ground:
            self.autothrottle.flight_phase = self.waypoint.flight_phase
        match self.autothrottle.flight_phase:
            case FlightPhase.TAKE_OFF:
                self.handle_takeoff()
            case FlightPhase.CLIMB:
                if hasattr(self, "TO_setting"):
                    del self.TO_setting
                self.handle_climb(self.waypoint)
            case FlightPhase.CRUISE:
                self.handle_cruise()
            case FlightPhase.DESCENT:
                return True
                self.handle_descent(self.waypoint, self.descent_angle)
            case FlightPhase.NULL:
                return True
            case _:
                logger.error("Invalid flight phase")
                raise ValueError("Invalid flight phase")

    def handle_takeoff(self):
        self.autothrottle()
    def handle_climb(self, waypoint: Fix):
        msl = self.aircraft.msl
        
        if self.autopilot.SpdMode:
            self.set_target_speed(self.aircraft.airplane.climb_v3)
        elif not self.above_10k and msl >= 10_000*unit.ft:
            if self.aircraft.landing_lights_status:
                self.aircraft.Landing_Lights_toggle
            if self.aircraft.seat_belt_status:
                self.aircraft.seat_belt_toggle
            self.set_target_speed(self.aircraft.airplane.climb_v2)
            self.above_10k = True
        elif msl <= 10_000*unit.ft and self.autothrottle.reached_target:
            self.set_target_speed(self.aircraft.airplane.climb_v1)

        self.autothrottle()
        delta_alt = waypoint.alt - msl
        dist = dist_to_fix(waypoint, self.fpl, self.aircraft)
        vs_sin = delta_alt.to(unit.m) / (dist.to(unit.m)**2 + delta_alt.to(unit.m)**2)**.5

        if msl != self.autopilot.Alt:
            self.autopilot.Vs = self.aircraft.gs * vs_sin

        sleep(1)
        
    def handle_cruise(self):
        delta_alt: Quantity = self.waypoint.alt - self.autopilot.Alt
        target_vs: Quantity = sign(delta_alt) * max((200*unit.fpm), min((1000*unit.fpm), abs(delta_alt / Vnav.time_target)))
        climb_time: Quantity = delta_alt / target_vs
        ete_fix: Quantity = dist_to_fix(self.waypoint, self.fpl, self.aircraft) / self.aircraft.gs - climb_time

        if ete_fix <= 0*unit.s:
            self.autopilot.Alt = self.waypoint.alt
            self.autopilot.Vs = target_vs
            self.vnav_wps = self.fpl.update_vnav_wps(self.aircraft) # not functioning right now
        elif ete_fix > 6 * 60*unit.s:
            logger.info(f"ETE to {self.waypoint.name}: {format_time(ete_fix.to(unit.s).m)}, ETA: {datetime.now() + timedelta(seconds=ete_fix.m)}")
            logger.info(f"sleeping for {format_time((ete_fix*0.5).m)}")
            sleep((ete_fix*0.5).m)
        else:
            logger.info(f"ETE to {self.waypoint.name}: {format_time(ete_fix.to(unit.s).m)}")
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

    def execute_holding(self, fix: Fix, Len: Quantity, width: Quantity, direction: Quantity, n_loop: int = 1) -> None:
        pos = self.aircraft.pos
        hdg = self.get_track_angle(pos, fix) + arcsin(self.aircraft.xwind / self.aircraft.tas)
        while cosine_law(pos, fix) > 1*unit.nm:
            self.autopilot.Hdg = hdg
            hdg = self.get_track_angle(pos, fix) + arcsin(self.aircraft.xwind / self.aircraft.tas)
            pos = self.aircraft.pos
            sleep(0.5)
        
        for _ in range(n_loop):
            hdg = direction + arcsin(self.aircraft.xwind / self.aircraft.tas)
            while dist_to_fix := (cosine_law(pos, fix)) > 1*unit.nm:
                condition = (
                    abs(self.aircraft.track - direction) > 5*unit.deg
                    and dist_to_fix >= Len,
                    
                    abs(dist_to_fix-width) < 5*unit.nm
                    and abs(self.aircraft.track - direction) > 5*unit.deg
                )
                if any(condition):
                    self.autopilot.Hdg = direction+arcsin(self.aircraft.xwind / self.aircraft.tas)+180*unit.deg
                    if self.autopilot.HdgOn:
                        self.autopilot.HdgOn = False
                    if not self.autopilot.BankOn:
                        self.autopilot.BankOn = True
                    self.autopilot.Bank = -arctan2(self.aircraft.tas**2, 9.81*unit.mps2 * width.to(unit.m)*0.5) * unit.rad
                else:
                    self.autopilot.Hdg = direction+arcsin(self.aircraft.xwind / self.aircraft.tas) + 180*unit.deg
                    if not self.autopilot.HdgOn:
                        self.autopilot.HdgOn = True
                    if self.autopilot.BankOn:
                        self.autopilot.BankOn = False
                        self.autopilot.Bank = 0
                pos = self.aircraft.pos


    @staticmethod
    def get_track_angle(fix1: Fix, fix2: Fix) -> Quantity:
        lat1, lon1, lat2, lon2 = fix1.lat, fix1.lon, fix2.lat, fix2.lon
        dlon = lon2 - lon1
        x = sin(dlon) * cos(lat2)
        y = cos(lat1) * sin(lat2) - sin(lat1) * cos(lat2) * cos(dlon)
        return arctan2(x, y)*unit.rad


    def __call__(self):
        # # if self.aircraft.dist_to_next <= 
        trg_track = self.get_track_angle(self.fpl[self.next_index-1], self.fpl[self.next_index])
        hdg = trg_track + arcsin(self.aircraft.xwind / self.aircraft.tas)
        self.autopilot.Hdg = hdg
        # true_track = self.get_track_angle(self.fpl[self.next_index], self.fpl[self.next_index+1])
        # variation = self.aircraft.send_command("magnetic_variation")
        # mag_track = true_track + variation
        # self.autopilot.Hdg += mag_track - self.autopilot.Hdg


def create_Fix(Start_Fix: Fix, bearing: Quantity, distance: Quantity) -> IFFPL:
    R = 6371e3*unit.m
    lat1, lon1 = Start_Fix.lat, Start_Fix.lon
    lat2 = arcsin(sin(lat1)*cos(distance.to(unit.m)/R) + cos(lat1)*sin(distance.to(unit.m).magnitude    )*cos(bearing.to(unit.rad)))
    lon2 = lon1 + arctan2(sin(bearing.to(unit.rad))*sin(distance.to(unit.m)/R)*cos(lat1.to(unit.rad)), cos(distance.to(unit.m)/R)-sin(lat1.to(unit.rad))*sin(lat2))
    return Fix("None", lat2, lon2, -1, -1)

def Only_Authothrottle(aircraft: Aircraft, autopilot: Autopilot, autothrottle: Autothrottle):
    logger.info("Starting autothrottle")
    while aircraft.is_on_ground:
        sleep(1)
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
    