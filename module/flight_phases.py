from module import ms2fpm, fpm2ms, ft2m, m2ft
from module import IFFPL, Fix, dist_to_fix, FlightPhase
from module import Aircraft, Autopilot, Autothrottle
from module import format_time
from module import logger

from numpy import arctan2, sin, sign, radians, degrees
# from datetime import datetime, timedelta
from time import sleep

dummy_fix = Fix("None", -1, -1, -1, -1)


def takeoff(aircraft: Aircraft, autopilot: Autopilot) -> None:
    if not aircraft.is_on_ground:
        return
    logger.info("Starting takeoff")
    k = None
    TO_setting: float = 0
    flex_temp: str = input("FLEX temperature : ") or ""
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
    while aircraft.n1 < 0.5 or (not aircraft.is_on_runway and aircraft.is_on_ground):
        sleep(1)
    autopilot.Throttle = TO_setting
    logger.info(f"Starting takeoff\nTO n1:{aircraft.n1_target:.2f}")
    while aircraft.is_on_ground or (aircraft.vs < fpm2ms(1100)): 
        sleep(1)
    if aircraft.is_on_ground:
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
    autothrottle = Autothrottle(aircraft, autopilot)

    
    while waypoint != dummy_fix:
        # setting the next "important" waypoint for the program 
        if aircraft.next_index > waypoint.index:
            waypoint = next(vnav_wps, dummy_fix)
            logger.info(f"Next waypoint: {waypoint.name} in {format_time(dist_to_fix(waypoint, fpl, aircraft)/aircraft.gs)}")
            continue

        if waypoint.flight_phase == FlightPhase.CLIMB:
            if autopilot.Alt != waypoint.alt:
                autopilot.Alt = waypoint.alt
            autothrottle(waypoint)
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
            delta_alt = waypoint.alt - autopilot.Alt
            dist = dist_to_fix(waypoint, fpl, aircraft)
            angle = arctan2(delta_alt, dist)
            target_vs = aircraft.gs * sin(angle)
            if angle > desced_angle:
                if autopilot.Alt != waypoint.alt:
                    autopilot.Alt = waypoint.alt
                autopilot.Vs = target_vs

def climbing_test(aircraft: Aircraft, autopilot: Autopilot, fpl: IFFPL):
    logger.info("Starting autothrottle")
    while aircraft.is_on_ground:
        sleep(1)
    autothrottle = Autothrottle(aircraft, autopilot)
    fix = Fix("None", -1, -1, -1, -1)
    fix._flight_phase = FlightPhase.CLIMB
    while aircraft.msl < autopilot.Alt:
        autothrottle(fix)
        sleep(1)
    