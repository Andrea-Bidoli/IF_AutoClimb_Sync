from module import m2ft, fpm2ms, knot2ms, ft2m, in_range, format_time
from numpy import arcsin, arctan2, radians, sin, sign, tan
from module.FlightPlan import IFFPL, Fix, dist_to_fix
from module.aircraft import Aircraft, Autopilot
from datetime import datetime, timedelta
from collections.abc import Generator
from module.logger import logger
from itertools import pairwise
from time import sleep

dummy_fix = Fix("None", -1, -1, -1, -1)

def calc_α(aircraft:Aircraft):
    # calculate angle of attack
    return arcsin(aircraft.vs / aircraft.tas)

def calc_γ(aircraft:Aircraft):
    # calculate slipstream angle
    aircraft.tas
    

def takeoff(aircraft: Aircraft, autopilot: Autopilot, DTO:int=1) -> None:
    if not aircraft.is_on_ground: return
    TO_setting: float = 0
    k = None
    try:
        k = aircraft.airplane.k
        if DTO >= aircraft.OAT and k is not None:
            TO_setting = (100 - k*(DTO-aircraft.OAT))/100
    except AttributeError:...

    if DTO > 2 and k is None:
        raise ValueError("Aircraft don't support FLEX TEMP")
    elif k is None:
        TO_setting = (100-DTO*10)/100

    while aircraft.n1 < .5 or (not aircraft.is_on_runway and aircraft.is_on_ground): sleep(1)
    autopilot.Throttle = TO_setting
    logger.info(f"Starting takeoff: {aircraft.n1_target:.2f}")


def climb_velocity(aircraft: Aircraft, autopilot: Autopilot) -> bool:
    if (aircraft.airplane is None): return False
    if (
        aircraft.msl >= ft2m(10_000) and
        not autopilot.SpdMode and
        not in_range(aircraft.ias, target_speed := knot2ms(aircraft.airplane.climb_v2), knot2ms(5))
    ):
        # seem to work, but need to deep test
        if (autopilot.SpdOn):
            autopilot.SpdOn = False
        if (autopilot.Spd != target_speed):
            autopilot.Spd = target_speed
        if (in_range(aircraft.ias, target_speed, knot2ms(5)) and aircraft.spd_change < 1):
            if (aircraft.n1_target > 0.9):
                autopilot.Vs -= fpm2ms(100)
                return True
            elif (aircraft.n1_target < 0.9):
                autopilot.Throttle = autopilot.Throttle + 0.1
            elif (aircraft.spd_change > 1 and aircraft.n1_target <= 0.9):
                autopilot.Throttle = autopilot.Throttle - 0.1
    elif (
        autopilot.SpdMode and
        in_range(aircraft.mach, (target_speed := aircraft.airplane.climb_v3), 0.01)
    ):
        # it 'loop' from mach reach to mach not reach
        if (autopilot.SpdOn):
            autopilot.SpdOn = False
        if (aircraft.mach < target_speed):
            if aircraft.n1_target > 0.9:
                autopilot.Vs -= fpm2ms(100)
            elif aircraft.n1_target < 0.9:
                autopilot.Throttle = autopilot.Throttle + 0.1
            elif aircraft.spd_change > 1 and aircraft.n1_target < 0.9:
                autopilot.Throttle = autopilot.Throttle - 0.1
    elif (not autopilot.SpdOn): autopilot.SpdOn = True
    return False

def climbing(aircraft:Aircraft, autopilot: Autopilot, fpl: IFFPL):
    def find_climb_wps(fpl:IFFPL) -> Generator[Fix, None, None]:
        for fix1, fix2 in pairwise(fpl):
            if fix1.altitude < fix2.altitude:
                yield fix2
            else:
                
                break
    
    climb_wps = find_climb_wps(fpl)
    waypoint = next(climb_wps, dummy_fix)
    while waypoint != dummy_fix:
        # maintain flight director
        if aircraft.next_index > waypoint._index:
            waypoint = next(climb_wps, dummy_fix)
            if waypoint.altitude > 0:
                autopilot.Alt = waypoint.altitude
            continue
        if aircraft.spd_change < 0 and not autopilot.SpdMode and not autopilot.SpdOn:
            autopilot.Vs -= fpm2ms(100)
            sleep(1)
            continue
        # change_spd part
        if aircraft.airplane is not None:
            if climb_velocity(aircraft, autopilot):
                continue
        delta_alt = waypoint.altitude - aircraft.msl
        dist = aircraft.dist_to_next
        angle = arctan2(delta_alt, dist)
        autopilot.Vs = aircraft.gs*sin(angle)
        sleep(1)

def cruise(aircraft: Aircraft, autopilot: Autopilot, fpl: IFFPL) -> None:
    def find_stepclimb_wps(fpl: IFFPL) -> Generator[Fix, None, None]:
        toc: bool = False
        for fix1, fix2 in pairwise(fpl):
            if fix1.name.lower() == "toc":
                toc = True
            if toc and fix1.altitude < fix2.altitude:
                yield fix2
            if fix2.name.lower() == "tod":
                break

    stepclimb_waypoints: Generator[Fix, None, None] = find_stepclimb_wps(fpl)
    waypoint: Fix|int = next(stepclimb_waypoints, dummy_fix)
    
    time_target:float = 2*60
    while waypoint != dummy_fix:
        if not autopilot.On: continue
        if fpl.index(waypoint) < aircraft.next_index:
            waypoint = next(stepclimb_waypoints, dummy_fix)
        logger.info(f"Next waypoint: {waypoint.name} in {format_time(aircraft.dist_to_next/aircraft.gs)}")
        delta_alt: float = waypoint.altitude - autopilot.Alt
        target_vs: float = sign(delta_alt)*max(fpm2ms(100), min(fpm2ms(1000), abs(delta_alt/time_target)))
        climb_time = delta_alt/target_vs
        ete_fix: float = dist_to_fix(waypoint, fpl, aircraft)/aircraft.gs - climb_time
        if ete_fix <= 0:
            logger.info(f"new Altitude: {m2ft(waypoint.altitude):.0f} Vs: {m2ft(target_vs):.0f} ETE: {format_time(ete_fix)}")
            autopilot.Alt = waypoint.altitude
            autopilot.Vs = target_vs
            waypoint = next(stepclimb_waypoints, dummy_fix)

        if ete_fix > 5*60:
            ete_fix *=0.85
            logger.info(f"Sleeping for {format_time(ete_fix)} awake at {datetime.now()+timedelta(seconds=ete_fix):%H:%M:%S}")
            sleep(ete_fix)
        else:
            sleep(10)

def descending(aircraft: Aircraft, autopilot: Autopilot, fpl: IFFPL):
    def descends_waypoints(fpl: IFFPL) -> Generator[Fix, None, None]:
        for fix1, fix2 in pairwise(fpl):
            if fix1.altitude >= fix2.altitude or aircraft.next_index >= fix1.index:
                continue
            yield fix1
    # def change_speed():
    #     if autopilot.SpdOn:
    #         autopilot.SpdOn = False
    #     if autopilot.Spd != target_speed:
    #         autopilot.Spd = target_speed if autopilot.SpdMode else knot2ms(target_speed)
    #     spd = aircraft.mach if autopilot.SpdMode else aircraft.ias
    #     if spd < target_speed:
    #         return
    #     if aircraft.n1_target <= 0 and aircraft.spd_change > 0:
    #             autopilot.Vs += fpm2ms(100)
    #     elif aircraft.n1_target > 0 and aircraft.spd_change > 0:
    #             autopilot.Throttle -= 0.1
    #     else:
    #         autopilot.SpdOn = True

    waypoints = descends_waypoints(fpl)
    waypoint = next(waypoints, dummy_fix)
    first_waypoint_index = waypoint.index
    while waypoint != dummy_fix:
        delta_alt = waypoint.altitude - autopilot.Alt
        descend_angle = radians(-3) if aircraft.next_index <= first_waypoint_index else arctan2(delta_alt, aircraft.dist_to_next)
        dist_tod = delta_alt/tan(descend_angle)
        if dist_to_fix(waypoint, fpl, aircraft) <= dist_tod:
            autopilot.Alt = waypoint.altitude
            autopilot.Vs = aircraft.tas*sin(descend_angle)
            waypoint = next(waypoints, dummy_fix)
        # TODO: add speed reduction in function of Alt(using model.database) and distance to destination
        # TODO: check optimal value to spd_change to count as positive (how many decimal places)
