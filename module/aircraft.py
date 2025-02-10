from .database import Airplane, retrive_airplane
from numpy import radians, arcsin, sign
from .logger import debug_logger
from .client import IFClient
from .FlightPlan import Fix, FlightPhase, IFFPL
from .utils import id_2_icao
from . import unit, Quantity
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
        self._Flaps_configs = range(self.send_command("flaps", "stops"))
    
    @property
    def Flaps_configs(self) -> range:
        return self._Flaps_configs

    ## Aircrafs status
    @property
    def msl(self) -> Quantity:
        ft = self.send_command("altitude_msl") * unit.ft
        return ft.to(unit.m)

    @property
    def agl(self) -> Quantity:
        ft = self.send_command("altitude_agl") * unit.ft
        return ft.to(unit.m)

    @property
    def tas(self) -> Quantity:
        return self.send_command("true_airspeed")*unit.ms

    @property
    def ias(self) -> Quantity:
        return self.send_command("indicated_airspeed")*unit.ms

    @property
    def gs(self) -> Quantity:
        return self.send_command("groundspeed")*unit.ms

    @property
    def mach(self) -> Quantity:
        return self.send_command("mach_speed")*unit.mach

    @property
    def hdg(self) -> Quantity:
        return self.send_command("heading_magnetic")*unit.rad

    @property
    def vs(self) -> Quantity:
        return self.send_command("vertical_speed") * unit.mpm

    @property
    def n1(self) -> Quantity:
        """return the N1 value of the engine if available, otherwise return the RPM value

        Returns:
            Quantity: N1 or RPM value
        """
        try:
            return round(self.send_command("0", "n1"), 2)*unit.percent
        except ValueError:
            return round(self.send_command("0", "rpm"), 2)*unit.rpm
    @property
    def n1_target(self) -> Quantity:
        try:
            return round(self.send_command("0", "n1_target"), 2)*unit.percent
        except ValueError:
            return -1*unit.dimensionless
    @property
    def thrust(self) -> Quantity:
        return round(self.send_command("0", "thrust_percentage"), 2)*unit.percent

    @property
    def thrust_target(self) -> Quantity:
        return round(self.send_command("0", "target_thrust_percentage"), 2)*unit.percent

    @property
    def pitch(self) -> Quantity:
        return self.send_command("pitch")*unit.rad

    @property
    def next_index(self) -> int:
        return self.send_command("flightplan", "next_waypoint_index")

    @property
    def dist_to_next(self) -> Quantity:
        Nm = self.send_command("flightplan", "next_waypoint_dist") * unit.nm
        return Nm.to(unit.m)

    @property
    def accel(self) -> Quantity:
        return self.send_command("acceleration", "z")*unit.ms/unit.s

    @property
    def spd_change(self) -> Quantity:
        return self.send_command("airspeed_change_rate")*unit.knot/unit.s

    @property
    def OAT(self) -> Quantity:
        return self.send_command("oat")*unit.celsius

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
        return self.send_command("landing_lights_controller/state")
    
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
    def α(self) -> Quantity:
        return (self.pitch.magnitude - arcsin(self.vs.magnitude / self.tas.magnitude))*unit.rad

    @property
    def γ(self) -> Quantity:
        crosswind = self.send_command("crosswind_component")
        return arcsin(crosswind / self.tas)

    @property
    def track(self) -> Quantity:
        return self.send_command("0/course")*unit.rad


class Autopilot(IFClient):
    def __init__(self, ip: str, port: int) -> None:
        super().__init__(ip, port)
        self.bank_angle = 30*unit.deg

    @property
    def Alt(self) -> Quantity:
        return self.send_command("alt", "target")*unit.m

    @property
    def Vs(self) -> Quantity:
        vs = self.send_command("vs", "target") * unit.mpm
        return vs.to(unit.fpm)

    @property
    def Spd(self) -> Quantity:
        spd = self.send_command("spd", "target")*unit.ms
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
    def Hdg(self) -> Quantity:
        return self.send_command("hdg", "target")*unit.rad

    @property
    def Bank(self) -> int:
        return self.send_command("bank", "target")*unit.rad

    @property
    def BankOn(self) -> bool:
        return self.send_command("bank", "on")

    @property
    def On(self) -> bool:
        return self.send_command("autopilot", "on")

    @property
    def vnavOn(self):
        return self.send_command("vnav/on")

    @Alt.setter
    def Alt(self, value: Quantity) -> None:
        self.send_command("alt", "target", write=True, data=value.to(unit.m).magnitude)

    @Vs.setter
    def Vs(self, value: Quantity) -> None:
        self.send_command("vs", "target", write=True, data=value.to(unit.mpm).magnitude)

    @Spd.setter
    def Spd(self, value: Quantity) -> None:
        self.send_command("spd", "target", write=True, data=value.to(unit.ms).magnitude)

    @Hdg.setter
    def Hdg(self, value: Quantity) -> None:
        self.send_command("hdg", "target", write=True, data=value.to(unit.rad).magnitude)

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
    
    @Bank.setter
    def Bank(self, value: Quantity) -> None:
        self.send_command("bank", "target", write=True, data=value.to(unit.rad).magnitude)


class Autothrottle:
    def __init__(self, aircraft: Aircraft, autopilot: Autopilot, fpl: IFFPL) -> None:
        self.aircraft = aircraft
        self.autopilot = autopilot
        self.fpl = fpl
        self.reach_target = False
        self.current_spd = None
        self.current_acc = None
        self.target_acc = 9 * unit.ms/unit.s  # ~1.1 knot/s
        self._target_spd:Quantity = None
    
    @property
    def Throttle(self) -> Quantity:
        value = self.aircraft.send_command("simulator", "throttle")
        return round((1000 - value) / 2000, 2)*unit.percent
    
    @Throttle.setter
    def Throttle(self, value: Quantity) -> None:
        value = int(value.to(unit.percent).magnitude * -2000 + 1000)
        self.aircraft.send_command("simulator", "throttle", write=True, data=value)
    
    @property
    def target_spd(self) -> Quantity:
        return self._target_spd
    
    @target_spd.setter
    def target_spd(self, value: Quantity) -> None:
        if self.autopilot.Spd != value:
            self._target_spd = value
            self.autopilot.Spd = value

    def set_target_speed(self, speed: Quantity) -> None:
        self.target_spd = speed
        self.reach_target = False
        self.autopilot.SpdOn = False
    
    def __call__(self, fix: Fix) -> None:
        if fix.flight_phase == FlightPhase.CLIMB:
            self._change_spd_climb()
        elif fix.flight_phase == FlightPhase.CRUISE:
            self._change_spd_climb()
        elif fix.flight_phase == FlightPhase.DESCENT:
            self._change_spd_descend()

    def _change_spd_climb(self) -> None:
        self.current_spd = self.aircraft.mach if self.autopilot.SpdMode else self.aircraft.ias
        self.current_acc = self.aircraft.accel * -1e3
        spd_tol = 0.01 if self.autopilot.SpdMode else (3*unit.knot).to(unit.mps).magnitude
        
        if not isclose(self.current_spd, self.target_spd, abs_tol=spd_tol) and not self.reach_target:
            delta_throttle = self.calc_delta_throttle()
            debug_logger.debug(f"Delta throttle: {delta_throttle}")
            if delta_throttle != 0 and not self.autopilot.SpdOn:
                self.Throttle += delta_throttle
        else:
            self.reach_target = True
            self.autopilot.SpdOn = True

    def _change_spd_descend(self) -> None:
        self.current_spd = self.aircraft.mach if self.autopilot.SpdMode else self.aircraft.ias
        self.current_acc = self.aircraft.accel * -1e3
        spd_tol = 0.01 if self.autopilot.SpdMode else (3*unit.knot).to(unit.mps).magnitude
        
        if self.Throttle <= 0 and self.current_acc >= 0:
            self.autopilot.Vs += 100  # Increase vertical speed to counter acceleration
        
        if not isclose(self.current_spd, self.target_spd, abs_tol=spd_tol) and not self.reach_target:
            delta_throttle = self.calc_delta_throttle()
            debug_logger.debug(f"Delta throttle: {delta_throttle}")
            if delta_throttle != 0 and not self.autopilot.SpdOn:
                self.Throttle += delta_throttle
        else:
            self.reach_target = True
            self.autopilot.SpdOn = True
    
    def calc_delta_throttle(self) -> Quantity:
        if isclose(self.current_acc, self.target_acc, rel_tol=5e-3):
            return 0
        
        delta_spd = self.target_spd - self.current_spd
        delta_acc = sign(delta_spd)*self.target_acc - self.current_acc
        debug_logger.debug(f"Delta acc: {delta_acc}")

        delta = sign(delta_acc) * (0.05 if abs(delta_acc) > abs(self.target_acc*.5) else 0.01)
        debug_logger.debug(f"Delta: {delta_acc}")
        debug_logger.debug(f"delta_throttle: {delta}")
        return delta
