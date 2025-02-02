from .database import Airplane, retrive_airplane
from numpy import radians, arcsin, sign
from .logger import debug_logger
from .client import IFClient
from .FlightPlan import Fix, FlightPhase
from .utils import id_2_icao
from .convertion import knot2ms, ft2m
from math import isclose
from enum import Enum

class Aircraft(IFClient):
    def __init__(self, ip: str, port: int) -> None:
        super().__init__(ip, port)
        tmp = self.send_command("aircraft/0/name")
        tmp = id_2_icao.get(tmp, "0xdd")
        self.airplane: Airplane = retrive_airplane(tmp)
        if self.airplane is None:
            debug_logger.warning(
                f"Airplane {self.send_command('aircraft/0/name')} not found in database"
            )
        self._Flaps_configs = range(self.send_command("flaps", "stops"))
    
    @property
    def Flaps_configs(self) -> range:
        return self._Flaps_configs

    ## Aircrafs status
    @property
    def msl(self) -> float:
        return self.send_command("altitude_msl") * 0.3048

    @property
    def agl(self) -> float:
        return self.send_command("altitude_agl") * 0.3048

    @property
    def tas(self) -> float:
        return self.send_command("true_airspeed")

    @property
    def ias(self) -> float:
        return self.send_command("indicated_airspeed")

    @property
    def gs(self) -> float:
        return self.send_command("groundspeed")

    @property
    def mach(self) -> float:
        return self.send_command("mach_speed")

    @property
    def hdg(self) -> float:
        return self.send_command("heading_magnetic")

    @property
    def vs(self) -> float:
        return self.send_command("vertical_speed")

    @property
    def n1(self) -> float:
        """return the N1 value of the engine if available, otherwise return the RPM value

        Returns:
            float: N1 or RPM value
        """
        try:
            return round(self.send_command("0", "n1"), 2)
        except ValueError:
            return round(self.send_command("0", "rpm"), 2)
    @property
    def n1_target(self) -> float:
        try:
            return round(self.send_command("0", "n1_target"), 2)
        except ValueError:
            return -1
    @property
    def thrust(self) -> float:
        return round(self.send_command("0", "thrust_percentage"), 2)

    @property
    def thrust_target(self) -> float:
        return round(self.send_command("0", "target_thrust_percentage"), 2)

    @property
    def pitch(self) -> float:
        return self.send_command("pitch")

    @property
    def next_index(self) -> int:
        return self.send_command("flightplan", "next_waypoint_index")

    @property
    def dist_to_next(self) -> float:
        return self.send_command("flightplan", "next_waypoint_dist") * 1852

    @property
    def accel(self) -> float:
        return self.send_command("acceleration", "z")

    @property
    def spd_change(self) -> float:
        return self.send_command("airspeed_change_rate")

    @property
    def OAT(self) -> float:
        return self.send_command("oat")

    @property
    def is_on_runway(self) -> bool:
        return self.send_command("is_on_runway")

    @property
    def is_on_ground(self) -> bool:
        return self.send_command("is_on_ground")

    @property
    def pos(self) -> Fix:
        name = self.send_command("aircraft/0/name")
        lat = self.send_command("0/latitude")
        lon = self.send_command("0/longitude")
        return Fix(name, self.msl, lat, lon, self.next_index-1)

    @property
    def elevator(self) -> int:
        return self.send_command("axes/pitch")

    @elevator.setter
    def elevator(self, value: int) -> None:
        value = max(-1000, min(value, 1000))
        self.send_command("axes", "0", "value", write=True, data=value)

    @property
    def trim(self) -> int:
        return self.send_command("axes/elevator_trim")

    @trim.setter
    def trim(self, value: int) -> None:
        if -100 < value < 100:
            value *= 10
        value = max(-1000, min(value, 1000))
        self.send_command("axes/elevator_trim", write=True, data=value)

    @property
    def Landing_gear_toggle(self) -> bool:
        self.send_command("LandingGear", write=True)

    @property
    def Landing_Lights_toggle(self) -> bool:
        self.send_command("LandingLights", write=True)

    @property
    def landing_lights_status(self) -> None:
        return self.send_command("landing_lights_switch/state")
    
    @property
    def seat_belt_status(self) -> bool:
        return bool(self.send_command("seatbelt"))
    @property
    def seat_belt_toggle(self) -> None:
        self.send_command("seatbelt", write=True, data= ( not self.seat_belt_status))

    @property
    def landing_gear_status(self) -> bool:
        return bool(self.send_command("landing_gear/animation_state"))

    @property
    def Flaps(self) -> int:
        return self.send_command("flaps", "state")

    @Flaps.setter
    def Flaps(self, value: int) -> None:
        value = max(0, min(value, len(self.Flaps_configs)-1))
        self.send_command("flaps", "state", write=True, data=value)

    @property
    def α(self) -> float:
        return self.pitch - arcsin(self.vs / self.tas)

    @property
    def γ(self) -> float:
        crosswind = self.send_command("crosswind_component")
        return arcsin(crosswind / self.tas)

    @property
    def track(self) -> float:
        return self.send_command("0/course")


class Autopilot(IFClient):
    def __init__(self, ip: str, port: int) -> None:
        super().__init__(ip, port)
        self.bank_angle = radians(30)

    @property
    def Alt(self) -> float:
        return self.send_command("alt", "target")

    @property
    def Vs(self) -> float:
        return self.send_command("vs", "target") / 60

    @property
    def Spd(self) -> float:
        spd = self.send_command("spd", "target")
        return spd

    @property
    def SpdMode(self) -> int:
        return self.send_command("spd", "mode")

    @property
    def HdgOn(self) -> bool:
        return self.send_command("hdg", "on")

    @property
    def AltOn(self) -> bool:
        return self.send_command("alt", "on")

    @property
    def VsOn(self) -> bool:
        return self.send_command("vs", "on")

    @property
    def SpdOn(self) -> bool:
        return self.send_command("spd", "on")

    @property
    def Hdg(self) -> float:
        return self.send_command("hdg", "target")

    @property
    def Bank(self) -> int:
        return self.send_command("bank", "target")

    @property
    def BankOn(self) -> bool:
        return self.send_command("bank", "on")

    @property
    def On(self) -> bool:
        return self.send_command("autopilot", "on")

    @property
    def Throttle(self) -> float:
        value = self.send_command("simulator", "throttle")
        return round((1000 - value) / 2000, 2)

    @property
    def vnavOn(self):
        return self.send_command("vnav/on")

    @Alt.setter
    def Alt(self, value: float) -> None:
        self.send_command("alt", "target", write=True, data=value)

    @Vs.setter
    def Vs(self, value: float) -> None:
        self.send_command("vs", "target", write=True, data=value * 60)

    @Spd.setter
    def Spd(self, value: float) -> None:
        self.send_command("spd", "target", write=True, data=value)

    @Hdg.setter
    def Hdg(self, value: float) -> None:
        self.send_command("hdg", "target", write=True, data=value)

    @Throttle.setter
    def Throttle(self, value: float) -> None:
        value = max(0, min(1, value))
        value = int(value * -2000 + 1000)
        self.send_command("simulator", "throttle", write=True, data=value)

    @SpdOn.setter
    def SpdOn(self, value: bool) -> None:
        self.send_command("spd", "on", write=True, data=value)

    @AltOn.setter
    def AltOn(self, value: bool) -> None:
        self.send_command("alt", "on", write=True, data=value)

    @VsOn.setter
    def VsOn(self, value: bool) -> None:
        self.send_command("vs", "on", write=True, data=value)

    @HdgOn.setter
    def HdgOn(self, value: bool) -> None:
        self.send_command("hdg", "on", write=True, data=value)

    @BankOn.setter
    def BankOn(self, value: bool) -> None:
        self.send_command("bank", "on", write=True, data=value)


class Autothrottle:

    @property
    def target_spd(self) -> float:
        return self._target_spd
    @target_spd.setter
    def target_spd(self, value: float) -> None:
        if self.autopilot.Spd != value:
            self._target_spd = value
            self.autopilot.Spd = value

    def __init__(self, aircraft: Aircraft, autopilot: Autopilot) -> None:
        self.above_10k: bool = False
        self.airplane: Airplane = aircraft.airplane
        self.aircraft: Aircraft = aircraft
        self.autopilot: Autopilot = autopilot
        self._target_spd: float = None
        if self.autopilot.SpdMode:
            self.target_spd: float = self.airplane.climb_v3
        elif self.aircraft.msl >= ft2m(10_000):
            self.above_10k = True
            self.target_spd: float = knot2ms(self.airplane.climb_v2)
        else:
            self.target_spd: float = knot2ms(self.airplane.climb_v1)
        debug_logger.debug(f"Target speed: {self.target_spd}")
        self.current_spd: float = None
        self.current_acc: float = None
        self.target_acc: float = 9 # ~ 1.1 knot/s
        self.reach_target: bool = False

    def _change_spd_climb(self) -> None:
        self.current_spd = self.aircraft.mach if self.autopilot.SpdMode else self.aircraft.ias
        self.current_acc = self.aircraft.accel * -1e3

        spd_tol = 0.01 if self.autopilot.SpdMode else knot2ms(3)

        if not isclose(self.current_spd, self.target_spd, abs_tol=spd_tol) and not self.reach_target:
            delta_spd = self.target_spd - self.current_spd
            self.target_acc *= sign(delta_spd)
            delta_throttle = self.calc_delta_throttle()
            debug_logger.debug(f"Delta throttle: {delta_throttle}")
            if delta_throttle != 0 and not self.autopilot.SpdOn:
                self.autopilot.Throttle += delta_throttle

        elif not self.reach_target:
            self.reach_target = True
            self.autopilot.SpdOn = True


    def __call__(self, fix: Fix):
        if fix.flight_phase == FlightPhase.CLIMB:
            self.climb_call()
        elif fix.flight_phase == FlightPhase.DESCENT:
            self.descend_call()
        else:
            return

    def climb_call(self) -> None:
        if self.airplane is not None:
            if (self.autopilot.SpdMode and not isclose(self.target_spd, self.airplane.climb_v3, abs_tol=1e-4)):
                self.reach_target = False
                self.autopilot.SpdOn = False
                self.target_spd = self.airplane.climb_v3
            elif (self.aircraft.msl >= ft2m(10_000) and not self.above_10k):
                self.target_spd = knot2ms(self.airplane.climb_v2)
                self.reach_target = False
                self.autopilot.SpdOn = False
                self.above_10k = True
            self._change_spd_climb()

    def descend_call(self) -> None:
        if self.airplane is not None:
            # TODO: add this implementation
            if self.autopilot.SpdMode:
                self.target_spd = self.airplane.descent_v1
            elif self.aircraft.msl <= ft2m(12_000) and self.above_10k:
                self.target_spd = knot2ms(self.airplane.descent_v1)
                self.above_10k = False
            elif not self.autopilot.SpdMode:
                self.target_spd = knot2ms(self.airplane.descent_v2)
            ...
    
    def _change_spd_descend(self) -> None:
        # TODO: add this implementation
        ...

    def calc_delta_throttle(self) -> float:
        if isclose(self.current_acc, self.target_acc, rel_tol=5e-3):
            delta_acc = 0

        else:
            delta_acc = self.target_acc - self.current_acc
            debug_logger.debug(f"Delta acc: {delta_acc}")

        if delta_acc == isclose(delta_acc, 0, abs_tol=0.1, rel_tol=1e-4):
            return 0

        elif abs(delta_acc) > 10:
            delta = sign(delta_acc) * 0.05
            debug_logger.debug(f"Delta: {delta_acc}")
            debug_logger.debug(f"delta_throttle: {delta}")
            return delta

        else:
            delta = sign(delta_acc) * 0.01
            debug_logger.debug(f"Delta: {delta_acc}")
            debug_logger.debug(f"delta_throttle: {delta}")
            return delta