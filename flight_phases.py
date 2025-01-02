from module.convertion import m2ft, fpm2ms, knot2ms, ft2m, ms2knot
from module.FlightPlan import IFFPL, Fix, dist_to_fix
from module.convertion import calc_delta_throttle
from module.aircraft import Aircraft, Autopilot
from module.logger import logger, debug_logger
from numpy import arctan2, radians, sin, sign
from module import in_range, format_time
from datetime import datetime, timedelta
from collections.abc import Generator
from time import sleep

dummy_fix = Fix("None", -1, -1, -1, -1)


def takeoff(aircraft: Aircraft, autopilot: Autopilot) -> None:
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
        raise ValueError("Aircraft don't support FLEX TEMP")
    elif DTO <= 2 and TO_setting == 0:
        TO_setting = (100 - DTO * 10) / 100

    print(f"Flex temp: {DTO} TO setting: {TO_setting}")
    while aircraft.n1 < 0.5 or (not aircraft.is_on_runway and aircraft.is_on_ground):
        sleep(1)
    autopilot.Throttle = TO_setting
    logger.info(f"Starting takeoff: {aircraft.n1_target:.2f}")
    while aircraft.is_on_ground or (aircraft.vs > fpm2ms(100) and aircraft.agl <= ft2m(300)): sleep(1)
    aircraft.Landing_gear_toggle


def change_spd(target: int, current: float, autopilot: Autopilot, aircraft: Aircraft) -> None:
    debug_logger.debug(f"Change speed function started, {target}")
    if (ms2knot(autopilot.Spd) != ms2knot(target)):
        autopilot.SpdOn = False
        autopilot.Spd = target
    tol = 0.01 if autopilot.SpdMode else 3
    if not in_range(current, target, tol):
        delta_throttle = calc_delta_throttle(aircraft.spd_change, 1, aircraft)
        debug_logger.debug(f"Delta throttle: {delta_throttle}")
        if delta_throttle != 0:
            autopilot.Throttle += delta_throttle
    else:
        autopilot.SpdOn = True

def climbing(aircraft: Aircraft, autopilot: Autopilot, fpl: IFFPL):
    if fpl is None: climbing_test(aircraft, autopilot)
    else:
        stpclb_wps = fpl.find_climb_wps()

        while aircraft.is_on_ground:
            sleep(1)

        waypoint = dummy_fix

        while True:
            if aircraft.next_index > waypoint.index:
                waypoint = next(stpclb_wps, dummy_fix)
                if waypoint == dummy_fix: break
                logger.info(f"Next waypoint: {waypoint.name} in {format_time(dist_to_fix(waypoint, fpl, aircraft)/aircraft.gs)}")
                if waypoint.alt > 0:
                    autopilot.Alt = waypoint.alt
                continue
            # change_spd part
            if aircraft.airplane is not None:
                # curr_speed = aircraft.mach if autopilot.SpdMode else aircraft.ias
                target_spd = aircraft.airplane.climb_v1
                if (autopilot.SpdMode and autopilot.Spd != aircraft.airplane.climb_v3):
                    target_spd = aircraft.airplane.climb_v3
                elif (aircraft.msl >= ft2m(10_000)):
                    aircraft.Landing_Lights_toggle
                    target_spd = aircraft.airplane.climb_v2
                current = aircraft.mach if autopilot.SpdMode else aircraft.ias
                change_spd(target_spd, current, autopilot, aircraft)
            
            # maintain flight director to change altitude
            delta_alt = waypoint.alt - aircraft.msl
            dist = aircraft.dist_to_next
            angle = arctan2(delta_alt, dist)
            autopilot.Vs = aircraft.gs * sin(angle) 
            sleep(1)


def cruise(aircraft: Aircraft, autopilot: Autopilot, fpl: IFFPL):
    stepclimb_waypoints: Generator[Fix, None, None] = fpl.find_stepclimb_wps()
    waypoint: Fix = next(stepclimb_waypoints, dummy_fix)

    time_target: float = 2 * 60
    while waypoint != dummy_fix:
        if not autopilot.On:
            continue
        if waypoint.index < aircraft.next_index:
            waypoint = next(stepclimb_waypoints, dummy_fix)
            continue
        logger.info(
            f"Next waypoint: {waypoint.name} in {format_time(dist_to_fix(waypoint, fpl, aircraft)/aircraft.gs)}"
        )
        delta_alt: float = waypoint.alt - autopilot.Alt
        target_vs: float = sign(delta_alt) * max(
            fpm2ms(200), min(fpm2ms(1000), abs(delta_alt / time_target))
        )
        climb_time = delta_alt / target_vs
        ete_fix: float = dist_to_fix(waypoint, fpl, aircraft) / aircraft.gs - climb_time
        if ete_fix <= 0:
            logger.info(
                f"new Altitude: {m2ft(waypoint.alt):.0f} Vs: {m2ft(target_vs):.0f} ETE: {format_time(ete_fix)}"
            )
            autopilot.Alt = waypoint.alt
            autopilot.Vs = target_vs
            aircraft.trim += aircraft.elevator
            continue

        if ete_fix > 5 * 60:
            ete_fix *= 0.85
            logger.info(
                f"Sleeping for {format_time(ete_fix)} awake at {datetime.now()+timedelta(seconds=ete_fix):%H:%M:%S}"
            )
            ## need to check how to update the fpl
            # fpl = IFFPL(aircraft.send_command("full_info"))
            # stepclimb_waypoints = fpl.find_stepclimb_wps()
            sleep(ete_fix)
        else:
            sleep(10)


def descending(aircraft: Aircraft, autopilot: Autopilot, fpl: IFFPL):
    def change_speed():
        if autopilot.SpdOn:
            autopilot.SpdOn = False
        if autopilot.Spd != target_speed:
            autopilot.Spd = target_speed if autopilot.SpdMode else knot2ms(target_speed)
        spd = aircraft.mach if autopilot.SpdMode else aircraft.ias
        if spd < target_speed:
            return
        if aircraft.n1_target <= 0 and aircraft.accel > 0:
            autopilot.Vs += fpm2ms(100)
        elif aircraft.n1_target > 0 and aircraft.accel > 0:
            autopilot.Throttle -= 0.1
        else:
            autopilot.SpdOn = True

    waypoints = fpl.find_descent_wps()
    waypoint = next(waypoints, dummy_fix)
    target_speed = aircraft.airplane.descent_v1
    standard_descend = radians(-2)
    while waypoint != dummy_fix:
        delta_alt = waypoint.alt - aircraft.msl
        calc_descend_angle = arctan2(delta_alt, dist_to_fix(waypoint, fpl, aircraft))

        descend_angle = standard_descend if calc_descend_angle < standard_descend else calc_descend_angle
        # TODO: calculate where is the TOD
        dist_tod = 0
        if dist_to_fix(waypoint, fpl, aircraft) <= dist_tod:
            autopilot.Alt = waypoint.alt
            autopilot.Vs = aircraft.tas * sin(descend_angle)
            waypoint = next(waypoints, dummy_fix)

        if aircraft.msl <= ft2m(2000) and aircraft.landing_gear_status <= 0:
            aircraft.Landing_gear_toggle
        # TODO: add speed reduction in function of Alt(using model.database) and distance to destination
        # TODO: check optimal value to accel to count as positive (how many decimal places)

def climbing_test(aircraft: Aircraft, autopilot: Autopilot):
    while aircraft.is_on_ground:
        sleep(1)

    while aircraft.msl < autopilot.Alt:
        # change_spd part
        if aircraft.airplane is not None:
            # curr_speed = aircraft.mach if autopilot.SpdMode else aircraft.ias
            target_spd = knot2ms(aircraft.airplane.climb_v1)
            if (autopilot.SpdMode and autopilot.Spd != aircraft.airplane.climb_v3):
                target_spd = aircraft.airplane.climb_v3
            elif (aircraft.msl >= ft2m(10_000)):
                target_spd = knot2ms(aircraft.airplane.climb_v2)
            current = aircraft.mach if autopilot.SpdMode else aircraft.ias
            change_spd(target_spd, current, autopilot, aircraft)
        sleep(1)