from module import ms2fpm, fpm2ms, ft2m, m2ft
from module import IFFPL, Fix, dist_to_fix, FlightPhase
from module import Aircraft, Autopilot, Autothrottle
from module import format_time
from module import logger, debug_logger

from numpy import arctan2, sin, sign, radians
from numpy import cos, arccos, sqrt, arcsin
# from datetime import datetime, timedelta
from time import sleep
from math import isclose

dummy_fix = Fix("None", -1, -1, -1, -1)




def takeoff(aircraft: Aircraft, autopilot: Autopilot) -> None:
    global flap_spd
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

    # set the flap retracting speed (in knots)
    # try:
    #     flap_spd = abs(int(flap_spd))
    # except ValueError:
    #     flap_spd = 200
            
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

    
def vnav(aircraft: Aircraft, autopilot: Autopilot, fpl: IFFPL):
    if fpl is None: 
        logger.warning("No flight plan found, unable to perfom VNAV")
        return
    logger.info("Starting VNAV")
    vnav_wps = fpl.update_vnav_wps(aircraft)
    waypoint = next(vnav_wps, dummy_fix)
    desced_angle = radians(2)
    time_target = 2 * 60
    if aircraft.airplane is not None:
        autothrottle = Autothrottle(aircraft, autopilot)

    
    while waypoint != dummy_fix:
        # setting the next "important" waypoint for the program 
        if aircraft.next_index > waypoint.index:
            waypoint = next(vnav_wps, dummy_fix)
            logger.info(f"Next waypoint: {waypoint.name} in {format_time(dist_to_fix(waypoint, fpl, aircraft)/aircraft.gs)}")
            continue


        match waypoint.flight_phase:
            case FlightPhase.CLIMB:
                if autopilot.Alt != waypoint.alt:
                    autopilot.Alt = waypoint.alt
                if aircraft.airplane is not None:
                    autothrottle(waypoint)
                if aircraft.msl >= ft2m(10_000) and aircraft.landing_lights_status:
                    if aircraft.landing_lights_status:
                        aircraft.Landing_Lights_toggle
                    if aircraft.seat_belt_status:
                        aircraft.seat_belt_toggle

                delta_alt = waypoint.alt - aircraft.msl
                dist = dist_to_fix(waypoint, fpl, aircraft)
                angle = arctan2(delta_alt, dist)
                autopilot.Vs = aircraft.gs * sin(angle)
                sleep(1)

            case FlightPhase.CRUISE:
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
        
            case FlightPhase.DESCENT:
                break
                delta_alt = waypoint.alt - autopilot.Alt
                dist = dist_to_fix(waypoint, fpl, aircraft)
                angle = arctan2(delta_alt, dist)
                target_vs = aircraft.gs * sin(angle)
                if angle > desced_angle:
                    if autopilot.Alt != waypoint.alt:
                        autopilot.Alt = waypoint.alt
                    autopilot.Vs = target_vs

class lnav:
    def __init__(self, aircraft: Aircraft, autopilot: Autopilot, fpl: IFFPL):
        self.aircraft = aircraft
        self.autopilot = autopilot
        self.fpl = fpl
        self.target_bank = radians(30)
        self.next_index = self.aircraft.next_index
        
    def __call__(self):
        p1, p2, p3 = self.fpl[self.next_index-1:self.next_index+1]
        
        p1 = cos(p1.lon)*cos(p1.lat), sin(p1.lon)*cos(p1.lat), sin(p1.lat)
        p2 = cos(p2.lon)*cos(p2.lat), sin(p2.lon)*cos(p2.lat), sin(p2.lat)
        p3 = cos(p3.lon)*cos(p3.lat), sin(p3.lon)*cos(p3.lat), sin(p3.lat)
        
        angle = arccos(p1*p2 + p2*p3 + p3*p1)
        target_track = self.aircraft.send_command("gps", "desired_track") + (radians(180) - angle)
        start_dist = 6371e3 * sqrt(1/sin(angle/2)**2 - 1)

        if self.aircraft.dist_to_next <= start_dist and not self.autopilot.BankOn:
            self.autopilot.HdgOn = False
            self.autopilot.Bank = self.target_bank
            self.autopilot.BankOn = True
        elif isclose(self.aircraft.track, target_track, abs_tol=radians(1), rel_tol=0.001):
            self.autopilot.BankOn = False
            self.autopilot.Hdg = target_track
            self.autopilot.HdgOn = True
            self.autopilot.Bank = 0



def Only_Authothrottle(aircraft: Aircraft, autopilot: Autopilot, fpl: IFFPL):
    logger.info("Starting autothrottle")
    while aircraft.is_on_ground:
        sleep(1)
    autothrottle = Autothrottle(aircraft, autopilot)
    fix = Fix("None", -1, -1, -1, -1)
    fix._flight_phase = FlightPhase.CLIMB
    while aircraft.msl < autopilot.Alt:
        if aircraft.msl >= ft2m(10_000) and aircraft.landing_lights_status:
            if aircraft.landing_lights_status:
                aircraft.Landing_Lights_toggle
            if aircraft.seat_belt_status:
                aircraft.seat_belt_toggle

        autothrottle(fix)
        sleep(1)
    