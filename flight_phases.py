from module import ms2fpm, fpm2ms, knot2ms, ft2m, m2ft
from module import IFFPL, Fix, dist_to_fix, FlightPhase
from module import Aircraft, Autopilot
from module import logger, debug_logger
from module import in_range, format_time
from module import Airplane

from numpy import arctan2, sin, sign, radians, degrees
# from datetime import datetime, timedelta
from time import sleep

dummy_fix = Fix("None", -1, -1, -1, -1)


class Autothrottle:
    def __init__(self, aircraft: Aircraft, autopilot: Autopilot) -> None:
        self.above_10k: bool = False
        self.airplane: Airplane = aircraft.airplane
        self.aircraft: Aircraft = aircraft
        self.autopilot: Autopilot = autopilot
        if self.airplane is None:
            self.target_spd: float = knot2ms(250)
        else:
            self.target_spd: float = knot2ms(self.airplane.climb_v1)
        self.current_spd: float = None
        self.current_acc: float = None
        self.target_acc: float = 0.8 # ~ 1 knot/s

    def _change_spd(self) -> None:
        self.current_spd = self.aircraft.mach if self.autopilot.SpdMode else self.aircraft.ias
        self.current_acc = self.aircraft.accel * -1e2

        if (not in_range(self.autopilot.Spd, self.target_spd, 1e-4)):
            self.autopilot.SpdOn = False
            self.autopilot.Spd = self.target_spd

        tol = 0.01 if self.autopilot.SpdMode else knot2ms(3)

        if not in_range(self.current_spd, self.target_spd, tol):
            delta_throttle = self.calc_delta_throttle()
            debug_logger.debug(f"Delta throttle: {delta_throttle}")
            if delta_throttle != 0:
                self.autopilot.Throttle += delta_throttle

        else:
            self.autopilot.SpdOn = True


    def __call__(self) -> None:
        if self.airplane is not None:    
            if (self.autopilot.SpdMode and not in_range(self.autopilot.Spd, self.airplane.climb_v3, 1e-4)):
                self.target_spd = self.airplane.climb_v3
            elif (self.aircraft.msl >= ft2m(10_000) and not self.above_10k):
                self.aircraft.Landing_Lights_toggle
                self.target_spd = knot2ms(self.airplane.climb_v2)
                self.above_10k = True
        else:
            if self.target_spd != self.autopilot.Spd:
                self.target_spd = self.autopilot.Spd
        self._change_spd()


    def calc_delta_throttle(self) -> float:
        
        if in_range(self.current_acc, self.target_acc, tollerance=0.05):
            delta_acc = 0
        
        else:
            delta_acc = round(self.target_acc - self.current_acc, 2)
            debug_logger.debug(f"Delta acc: {delta_acc}")
        
        if delta_acc == 0:
            return 0
        
        elif abs(delta_acc) > 0.1:
            # debug_logger.debug(f"Delta: {delta_acc}\ndelta_throttle: {sign(delta_acc) * 0.05}")
            return sign(delta_acc) * 0.05
        
        else:
            # debug_logger.debug(f"Delta: {delta_acc}\n{sign(delta_acc) * 0.01}")
            return sign(delta_acc) * 0.01


def takeoff(aircraft: Aircraft, autopilot: Autopilot) -> None:
    logger.info("Starting takeoff")
    if not aircraft.is_on_ground:
        return
    k = None
    TO_setting: float = 0
    flex_temp: int = input("FLEX temperature : ") or 1
    DTO = int(flex_temp)
    try:
        k = aircraft.airplane.k
        if DTO >= aircraft.OAT:
            TO_setting = (100 - k * (DTO - aircraft.OAT)) / 100
    except AttributeError: ...

    if DTO > 2 and TO_setting == 0:
        logger.warning("Aircraft don't support FLEX TEMP, please take off manually")
        return
    elif DTO <= 2 and TO_setting == 0:
        TO_setting = (100 - DTO * 10) / 100

    logger.info(f"Flex temp: {DTO} TO setting: {TO_setting}")
    while aircraft.n1 < 0.5 or (not aircraft.is_on_runway and aircraft.is_on_ground):
        sleep(1)
    autopilot.Throttle = TO_setting
    logger.info(f"Starting takeoff\nTO n1:{aircraft.n1_target:.2f}")
    while aircraft.is_on_ground or (aircraft.vs > fpm2ms(100) and aircraft.agl <= ft2m(100)): sleep(1)
    aircraft.Landing_gear_toggle


def vnav(aircraft: Aircraft, autopilot: Autopilot, fpl: IFFPL):
    if fpl is None: 
        logger.warning("No flight plan found, unable to perfom VNAV")
        return
    logger.info("Starting VNAV")
    autothrottle = Autothrottle(aircraft, autopilot)
    vnav_wps = fpl.update_vnav_wps(aircraft)
    waypoint = next(vnav_wps, dummy_fix)
    
    time_target = 2 * 60


    while waypoint != dummy_fix:
        # setting the next "important" waypoint for the program 
        if aircraft.next_index > waypoint.index:
            waypoint = next(vnav_wps, dummy_fix)
            logger.info(f"Next waypoint: {waypoint.name} in {format_time(dist_to_fix(waypoint, fpl, aircraft)/aircraft.gs)}")
            continue

        if waypoint.flight_phase == FlightPhase.CLIMB:
            if autopilot.Alt != waypoint.alt:
                autopilot.Alt = waypoint.alt
            autothrottle()
            delta_alt = waypoint.alt - aircraft.msl
            dist = dist_to_fix(waypoint, fpl, aircraft)
            angle = arctan2(delta_alt, dist)
            autopilot.Vs = aircraft.gs * sin(angle)
            sleep(1)

        elif waypoint.flight_phase == FlightPhase.CRUISE: 
            delta_alt = waypoint.alt - autopilot.Alt
            target_vs = sign(delta_alt) * max(fpm2ms(200), min(fpm2ms(1000), abs(delta_alt / time_target))) # calculate the target vertical speed for stepclimb
            climb_time = delta_alt / target_vs
            ete_fix = dist_to_fix(waypoint, fpl, aircraft) / aircraft.gs - climb_time # estimated time to fix
            
            if ete_fix <= 0:
                # changing the altitude and vertical speed of the aircraft
                logger.info(f"new Altitude: {m2ft(waypoint.alt):.0f} Vs: {ms2fpm(target_vs):.0f} ETE: {format_time(ete_fix)}")
                autopilot.Alt = waypoint.alt
                autopilot.Vs = target_vs
                vnav_wps = fpl.update_vnav_wps(aircraft)
                continue
            elif ete_fix > 6 * 60:
                logger.info(f"Next waypoint: {waypoint.name} in {format_time(dist_to_fix(waypoint, fpl, aircraft)/aircraft.gs)}")
                sleep(5*60)
            else:
                sleep(10)
        
        elif waypoint.flight_phase == FlightPhase.DESCENT:
            break

def climbing_test(aircraft: Aircraft, autopilot: Autopilot):
    while aircraft.is_on_ground:
        sleep(1)
    autothrottle = Autothrottle(aircraft, autopilot)
    while aircraft.msl < autopilot.Alt:
        # change_spd part
        autothrottle()
        sleep(1)