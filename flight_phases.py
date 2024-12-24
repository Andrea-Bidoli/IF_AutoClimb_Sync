from module.convertion import m2ft, fpm2ms, knot2ms, ft2m
from module import in_range, format_time
from numpy import arcsin, arctan2, radians, sin, sign
from module.FlightPlan import IFFPL, Fix, dist_to_fix
from module.aircraft import Aircraft, Autopilot
from datetime import datetime, timedelta
from module import calc_delta_throttle
from collections.abc import Generator
from module.logger import logger, debug_logger
from time import sleep

dummy_fix = Fix("None", -1, -1, -1, -1)


def calc_α(aircraft: Aircraft):
    # calculate angle of attack
    return arcsin(aircraft.vs / aircraft.tas)


def calc_γ(aircraft: Aircraft):
    # calculate slipstream angle
    aircraft.tas


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
    except AttributeError:
        ...

    if DTO > 2 and TO_setting == 0:
        raise ValueError("Aircraft don't support FLEX TEMP")
    elif DTO <= 2 and TO_setting == 0:
        TO_setting = (100 - DTO * 10) / 100

    print(f"Flex temp: {DTO} TO setting: {TO_setting}")
    while aircraft.n1 < 0.5 or (not aircraft.is_on_runway and aircraft.is_on_ground):
        sleep(1)
    autopilot.Throttle = TO_setting
    logger.info(f"Starting takeoff: {aircraft.n1_target:.2f}")


def change_spd(target_speed: int, autopilot: Autopilot, aircraft: Aircraft) -> Generator[bool, float, None]:
    target_speed = knot2ms(target_speed)
    bool_spd = False
    try:
        while True:
            current_speed = aircraft.mach if autopilot.SpdMode else aircraft.ias
            if not in_range(current_speed, target_speed, knot2ms(5)):
                delta = calc_delta_throttle(current_speed, target_speed, aircraft)
                if delta != 0:
                    autopilot.Throttle += delta
                else:
                    autopilot.Vs += fpm2ms(100)
                    bool_spd = not bool_spd
            else:
                autopilot.SpdOn = True
                bool_spd = not bool_spd

            new_speed = yield bool_spd
            if new_speed is not None:
                target_speed = new_speed if new_speed < 1 else knot2ms(new_speed)
                if autopilot.SpdMode and new_speed > 1: raise ValueError("Speed must be in mach when above 28000ft")
    except Exception as e:
        debug_logger.error(e, exc_info=True)
    finally:
        logger.warning("Change speed function ended")

# def change_spd(autopilot: Autopilot, aircraft: Aircraft) -> bool:
#     if autopilot.SpdOn:
#         autopilot.SpdOn = False
#     if autopilot.Spd != target_speed:
#         autopilot.Spd = target_speed
#     if not in_range(aircraft.ias, target_speed, knot2ms(5) if not autopilot.SpdMode else 0.01) and aircraft.accel < 1:
#         if aircraft.n1_target > 0.9:
#             autopilot.Vs -= fpm2ms(100)
#             return True
#         elif aircraft.n1_target < 0.9:
#             autopilot.Throttle = autopilot.Throttle + calc_delta_throttle(aircraft.n1_target, 0.9)
#         elif aircraft.accel > 1 and aircraft.n1_target <= 0.9:
#             autopilot.Throttle = autopilot.Throttle + calc_delta_throttle(aircraft.n1_target, 0.9)
#     return False


def climb_velocity(aircraft: Aircraft, autopilot: Autopilot) -> bool:

    if aircraft.airplane is None:
        return False
    chg_spd_gen = change_spd(aircraft.airplane.climb_v1, autopilot, aircraft)
    next(chg_spd_gen)
    # curr_speed = aircraft.mach if autopilot.SpdMode else aircraft.ias
    if (
        autopilot.Spd != knot2ms(aircraft.airplane.climb_v1) and
        aircraft.msl < ft2m(10_000)
    ):
        chg_spd_gen.send(knot2ms(aircraft.airplane.climb_v1))

    elif (
        aircraft.msl >= ft2m(10_000)
        and autopilot.Spd != knot2ms(aircraft.airplane.climb_v2)
    ):
        chg_spd_gen.send(knot2ms(aircraft.airplane.climb_v2))

    elif (autopilot.SpdMode and autopilot.Spd != aircraft.airplane.climb_v3): 
        chg_spd_gen.send(knot2ms(aircraft.airplane.climb_v3))
    # FIXME: test `in_range` function for mach speed
    return next(chg_spd_gen)


def climbing(aircraft: Aircraft, autopilot: Autopilot, fpl: IFFPL):
    climb_wps = fpl.find_climb_wps()
    waypoint = next(climb_wps, dummy_fix)
    while aircraft.is_on_ground: sleep(1)

    while waypoint != dummy_fix:
        # maintain flight director
        if aircraft.next_index > waypoint.index:
            waypoint = next(climb_wps, dummy_fix)
            logger.info(f"Next waypoint: {waypoint.name} in {format_time(dist_to_fix(waypoint, aircraft)/aircraft.gs)}")
            if waypoint.alt > 0:
                autopilot.Alt = waypoint.alt
            continue
        # change_spd part
        if aircraft.airplane is not None: 
            if climb_velocity(aircraft, autopilot): continue
        
        delta_alt = waypoint.alt - aircraft.msl
        dist = aircraft.dist_to_next
        angle = arctan2(delta_alt, dist)
        autopilot.Vs = aircraft.gs * sin(angle)
        sleep(1)


def cruise(aircraft: Aircraft, autopilot: Autopilot, fpl: IFFPL) -> None:
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
            fpm2ms(100), min(fpm2ms(1000), abs(delta_alt / time_target))
        )
        climb_time = delta_alt / target_vs
        ete_fix: float = dist_to_fix(waypoint, fpl, aircraft) / aircraft.gs - climb_time
        if ete_fix <= 0:
            logger.info(
                f"new Altitude: {m2ft(waypoint.alt):.0f} Vs: {m2ft(target_vs):.0f} ETE: {format_time(ete_fix)}"
            )
            autopilot.Alt = waypoint.alt
            autopilot.Vs = target_vs
            continue

        if ete_fix > 5 * 60:
            ete_fix *= 0.85
            logger.info(
                f"Sleeping for {format_time(ete_fix)} awake at {datetime.now()+timedelta(seconds=ete_fix):%H:%M:%S}"
            )
            fpl = IFFPL(aircraft.send_command("full_info"))
            stepclimb_waypoints = fpl.find_stepclimb_wps()
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
        # TODO: add speed reduction in function of Alt(using model.database) and distance to destination
        # TODO: check optimal value to accel to count as positive (how many decimal places)
