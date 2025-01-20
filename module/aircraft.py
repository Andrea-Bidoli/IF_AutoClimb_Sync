from .database import Airplane, retrive_airplane
from numpy import radians, arcsin, sign
from .logger import debug_logger
from .client import IFClient
from .FlightPlan import Fix, FlightPhase
from .utils import id_2_icao, get_tollerance
from .convertion import knot2ms, ft2m
from math import isclose

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
        return round(self.send_command("0", "n1"), 2)

    @property
    def n1_target(self) -> float:
        return round(self.send_command("1", "n1_target"), 2)

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
    def landing_gear_status(self) -> None:
        return self.send_command("landing_gear/animation_state")

    @property
    def α(self) -> float:
        return self.pitch - arcsin(self.vs / self.tas)

    @property
    def γ(self) -> float:
        crosswind = self.send_command("crosswind_component")
        return arcsin(crosswind / self.tas)


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
        self.target_acc: float = 16 # ~ 1 knot/s

    def _change_spd(self) -> None:
        self.current_spd = self.aircraft.mach if self.autopilot.SpdMode else self.aircraft.ias
        self.current_acc = self.aircraft.accel * -1e3

        if (not isclose(self.autopilot.Spd, self.target_spd, abs_tol=1e-4)):
            self.autopilot.SpdOn = False
            self.autopilot.Spd = self.target_spd

        spd_tol = 0.01 if self.autopilot.SpdMode else knot2ms(3)

        if not isclose(self.current_spd, self.target_spd, abs_tol=spd_tol):
            delta_spd = self.target_spd - self.current_spd
            self.target_acc *= sign(delta_spd)
            delta_throttle = self.calc_delta_throttle()
            debug_logger.debug(f"Delta throttle: {delta_throttle}")
            if delta_throttle != 0 and not self.autopilot.SpdOn:
                self.autopilot.Throttle += delta_throttle

        else:
            self.autopilot.SpdOn = True


    def __call__(self, fix: Fix):
        if fix.flight_phase == FlightPhase.CLIMB:
            self.climb_call()
        elif fix.flight_phase == FlightPhase.DESCENT:
            self.descend_call()

    def climb_call(self) -> None:
        if self.airplane is not None:    
            if (self.autopilot.SpdMode and not isclose(self.autopilot.Spd, self.airplane.climb_v3, abs_tol=1e-4)):
                self.target_spd = self.airplane.climb_v3
            elif (self.aircraft.msl >= ft2m(10_000) and not self.above_10k):
                self.aircraft.Landing_Lights_toggle
                self.target_spd = knot2ms(self.airplane.climb_v2)
                self.above_10k = True
        else:
            if self.target_spd != self.autopilot.Spd:
                self.target_spd = self.autopilot.Spd
        self._change_spd()

    def descend_call(self) -> None:
        # TODO: finish this implementation
        if self.airplane is not None:
            if (self.autopilot.SpdMode and not isclose(self.autopilot.Spd, self.airplane.descent_v1, abs_tol=1e-2)):
                self.target_spd = self.airplane.descent_v1
            elif (not self.autopilot.SpdMode and self.above_10k):
                self.target_spd = knot2ms(self.airplane.descent_v2)
            elif (self.aircraft.msl <= ft2m(10_000) and self.above_10k):
                self.aircraft.Landing_Lights_toggle
                self.above_10k = False
                self.target_spd = knot2ms(self.airplane.descent_v1)
            self._change_spd_descend()
    
    def _change_spd_descend(self) -> None:
        # TODO: finish this implementation
        self.current_spd = self.aircraft.mach if self.autopilot.SpdMode else self.aircraft.ias
        self.current_acc = self.aircraft.accel * -1e3

        if (not isclose(self.autopilot.Spd, self.target_spd, abs_tol=1e-4)):
            self.autopilot.SpdOn = False
            self.autopilot.Spd = self.target_spd

        spd_tol = 0.01 if self.autopilot.SpdMode else knot2ms(3)

        if not isclose(self.current_spd, self.target_spd, abs_tol=spd_tol):
            delta_spd = self.target_spd - self.current_spd
            self.target_acc *= sign(delta_spd)
            delta_throttle = self.calc_delta_throttle()
            debug_logger.debug(f"Delta throttle: {delta_throttle}")
            if delta_throttle != 0 and self.autopilot.Throttle > 0:
                self.autopilot.Throttle += delta_throttle
            elif delta_throttle != 0 and self.autopilot.Throttle == 0:
                if self.autopilot.Vs < -ft2m(800):
                    self.autopilot.Vs += ft2m(100)
                    return True
        else:
            self.autopilot.SpdOn = True
                
                

    def calc_delta_throttle(self) -> float:
        if isclose(self.current_acc, self.target_acc, abs_tol=5*get_tollerance(self.target_acc)):
            delta_acc = 0

        else:
            delta_acc = self.target_acc - self.current_acc
            debug_logger.debug(f"Delta acc: {delta_acc}")

        if delta_acc == 0:
            return 0

        elif abs(delta_acc) > 0.1:
            debug_logger.debug(f"Delta: {delta_acc}\ndelta_throttle: {sign(delta_acc) * 0.05}")
            return sign(delta_acc) * 0.05

        else:
            debug_logger.debug(f"Delta: {delta_acc}\n{sign(delta_acc) * 0.01}")
            return sign(delta_acc) * 0.01