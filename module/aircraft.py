from .database import Airplane, retrive_airplane
from .logger import debug_logger, logger
from .client import IFClient, Node
from .FlightPlan import Fix, FlightPhase, IFFPL
from .utils import id_2_icao
from . import unit, Quantity
from numpy import arcsin, sign, clip
from math import isclose
from time import sleep

from enum import Enum, auto
class Spd(Enum):
    Vr = auto()
    clb_V1 = auto()
    clb_V2 = auto()
    clb_V3 = auto()
    crz_V = auto()

class Flaps:
    def __init__(self, client: 'IFClient'):
        self.client: 'IFClient' = client
        self.manifest: 'Node' = client.manifest.search("configuration", "flaps")
        self.flap_stop = self.client.send_command("stops", self.manifest)
        for i in range(self.flap_stop):
            name = self.client.send_command(str(i), "name", self.manifest)
            setattr(self, name[:-1] if len(name) > 1 else name, i)
        self._current = self.client.send_command("flaps", "state")
    
    @property
    def state(self) -> int:
        return self._current

    @state.setter
    def state(self, value: int) -> None:
        if not (0 <= value < self.flap_stop):
            raise ValueError(f"Invalid value: {value}")
        else:
            self._current = value
            self.client.send_command("systems", "flaps", "state", write=True, data=value)

    def set(self, value: int) -> None:
        self.state = value

class Aircraft:
    def __init__(self, client: IFClient) -> None:
        self.client = client
        self.manifest = self.client.manifest.search("aircraft")
        aircraft_name = self.client.send_command("0", "name", self.manifest)
        aircraft_icao = id_2_icao.get(aircraft_name, "0xdd")
        self.airplane: Airplane = retrive_airplane(aircraft_icao)
        if self.airplane.icao is None:
            debug_logger.warning(
                f"Airplane {aircraft_name} not found in database"
            )
        self.Flaps = Flaps(client)    

    ## Aircrafs status
    @property
    def msl(self) -> Quantity:
        ft = self.client.send_command("altitude_msl") * unit.ft
        return ft.to(unit.m)

    @property
    def agl(self) -> Quantity:
        ft = self.client.send_command("altitude_agl") * unit.ft
        return ft.to(unit.m)

    @property
    def tas(self) -> Quantity:
        return self.client.send_command("true_airspeed")*unit.ms

    @property
    def ias(self) -> Quantity:
        return self.client.send_command("indicated_airspeed")*unit.ms

    @property
    def gs(self) -> Quantity:
        return self.client.send_command("groundspeed")*unit.ms

    @property
    def mach(self) -> Quantity:
        return self.client.send_command("mach_speed")*unit.mach

    @property
    def hdg(self) -> Quantity:
        return self.client.send_command("heading_magnetic")*unit.rad

    @property
    def vs(self) -> Quantity:
        return self.client.send_command("vertical_speed") * unit.mpm

    @property
    def n1(self) -> Quantity:
        """return the N1 value of the engine if available, otherwise return the RPM value

        Returns:
            Quantity: N1 or RPM value
        """
        try:
            return round(self.client.send_command("0", "n1"), 2)*unit.no_unit
        except ValueError:
            return round(self.client.send_command("0", "rpm"), 2)*unit.rpm
    @property
    def n1_target(self) -> Quantity:
        try:
            return round(self.client.send_command("0", "n1_target"), 2)*unit.no_unit
        except ValueError:
            return -1*unit.dimensionless
    @property
    def thrust(self) -> Quantity:
        return round(self.client.send_command("0", "thrust_percentage"), 2)*unit.no_unit

    @property
    def thrust_target(self) -> Quantity:
        return round(self.client.send_command("0", "target_thrust_percentage"), 2)*unit.no_unit

    @property
    def pitch(self) -> Quantity:
        return self.client.send_command("pitch")*unit.rad

    @property
    def next_index(self) -> int:
        return self.client.send_command("flightplan", "next_waypoint_index")

    @property
    def dist_to_next(self) -> Quantity:
        Nm = self.client.send_command("flightplan", "next_waypoint_dist") * unit.nm
        return Nm.to(unit.m)

    @property
    def accel(self) -> Quantity:
        return self.client.send_command("acceleration", "z")*unit.mps2

    @property
    def spd_change(self) -> Quantity:
        return self.client.send_command("airspeed_change_rate")*unit.knot/unit.s

    @property
    def OAT(self) -> Quantity:
        return self.client.send_command("oat")

    @property
    def is_on_runway(self) -> bool:
        return self.client.send_command("is_on_runway")

    @property
    def is_on_ground(self) -> bool:
        return self.client.send_command("is_on_ground")

    @property
    def pos(self) -> Fix:
        name = self.client.send_command("aircraft","0","name")
        lat = self.client.send_command("0", "latitude")
        lon = self.client.send_command("0", "longitude")
        return Fix(name, self.msl.magnitude, lat, lon, self.next_index-1)

    @property
    def elevator(self) -> int:
        return self.client.send_command("axes", "pitch")

    @elevator.setter
    def elevator(self, value: int) -> None:
        value = max(-1000, min(value, 1000))
        self.client.send_command("axes", "0", "value", write=True, data=value)

    @property
    def trim(self) -> int:
        return self.client.send_command("axes", "elevator_trim")

    @trim.setter
    def trim(self, value: int) -> None:
        if -100 < value < 100:
            value *= 10
        value = max(-1000, min(value, 1000))
        self.client.send_command("axes", "elevator_trim", write=True, data=value)

    @property
    def Landing_gear_toggle(self) -> bool:
        self.client.send_command("LandingGear", write=True)

    @property
    def Landing_Lights_toggle(self) -> bool:
        self.client.send_command("LandingLights", write=True)

    @property
    def landing_lights_status(self) -> None:
        return self.client.send_command("landing_lights_controller", "state")
    
    @property
    def seat_belt_status(self) -> bool:
        return bool(self.client.send_command("seatbelt"))
    @property
    def seat_belt_toggle(self) -> None:
        self.client.send_command("seatbelt", write=True, data= ( not self.seat_belt_status))

    @property
    def landing_gear_status(self) -> bool:
        return bool(self.client.send_command("landing_gear", "lever_state"))
        self.client.send_command("flaps", "state", write=True, data=value)

    @property
    def α(self) -> Quantity:
        return (self.pitch.magnitude - arcsin(self.vs.magnitude / self.tas.magnitude))*unit.rad

    @property
    def γ(self) -> Quantity:
        crosswind = self.client.send_command("crosswind_component")
        return arcsin(crosswind / self.tas)

    @property
    def track(self) -> Quantity:
        return self.client.send_command("0", "course")*unit.rad
    @property
    def xwind(self) -> Quantity:
        return self.client.send_command("crosswind_component")*unit.ms


class Autopilot:
    def __init__(self, client: IFClient) -> None:
        self.client = client
        self.manifest = self.client.manifest.search("systems", "autopilot")
    @property
    def Alt(self) -> Quantity:
        return self.client.send_command("alt", "target", self.manifest)*unit.m

    @property
    def Vs(self) -> Quantity:
        vs = self.client.send_command("vs", "target", self.manifest) * unit.mpm
        return vs.to(unit.fpm)

    @property
    def Spd(self) -> Quantity:
        spd = self.client.send_command("spd", "target", self.manifest)*unit.ms
        return spd

    @property
    def SpdMode(self) -> int:
        return self.client.send_command("spd", "mode", self.manifest)

    @property
    def HdgOn(self) -> bool:
        return self.client.send_command("hdg", "on", self.manifest)

    @property
    def AltOn(self) -> bool:
        return self.client.send_command("alt", "on", self.manifest)

    @property
    def VsOn(self) -> bool:
        return self.client.send_command("vs", "on", self.manifest)

    @property
    def SpdOn(self) -> bool:
        return self.client.send_command("spd", "on", self.manifest)

    @property
    def Hdg(self) -> Quantity:
        return self.client.send_command("hdg", "target", self.manifest)*unit.rad

    @property
    def Bank(self) -> int:
        return self.client.send_command("bank", "target", self.manifest)*unit.rad

    @property
    def BankOn(self) -> bool:
        return self.client.send_command("bank", "on", self.manifest)

    @property
    def On(self) -> bool:
        return self.client.send_command("on", self.manifest)

    @property
    def vnavOn(self):
        return self.client.send_command("vnav", "on", self.manifest)

    @property
    def lnavOn(self):
        return self.client.send_command("nav", "on", self.manifest)
    
    @lnavOn.setter
    def lnavOn(self, value: bool):
        
        self.client.send_command("nav", "on", self.manifest, write=True, data=value)
    @Alt.setter
    def Alt(self, value: Quantity) -> None:
        self.client.send_command("alt", "target", self.manifest, write=True, data=value.m_as(unit.m))

    @Vs.setter
    def Vs(self, value: Quantity) -> None:
        self.client.send_command("vs", "target", self.manifest, write=True, data=value.m_as(unit.mpm))

    @Spd.setter
    def Spd(self, value: Quantity) -> None:
        if self.SpdMode:
            value = value.m_as(unit.mach)
        else:
            value = value.m_as(unit.ms)
        self.client.send_command("spd", "target", self.manifest, write=True, data=value)

    @Hdg.setter
    def Hdg(self, value: Quantity) -> None:
        self.client.send_command("hdg", "target", self.manifest, write=True, data=value.m_as(unit.rad))

    @SpdOn.setter
    def SpdOn(self, value: bool) -> None:
        if self.SpdOn != value:
            self.client.send_command("spd", "on", self.manifest, write=True, data=value)

    @AltOn.setter
    def AltOn(self, value: bool) -> None:
        self.client.send_command("alt", "on", self.manifest, write=True, data=value)

    @VsOn.setter
    def VsOn(self, value: bool) -> None:
        self.client.send_command("vs", "on", self.manifest, write=True, data=value)

    @HdgOn.setter
    def HdgOn(self, value: bool) -> None:
        self.client.send_command("hdg", "on", self.manifest, write=True, data=value)

    @BankOn.setter
    def BankOn(self, value: bool) -> None:
        self.client.send_command("bank", "on", self.manifest, write=True, data=value)
    
    @Bank.setter
    def Bank(self, value: Quantity) -> None:
        self.client.send_command("bank", "target", self.manifest, write=True, data=value.m_as(unit.rad))


class Autothrottle:

    # initializer
    def __init__(self, aircraft: Aircraft, autopilot: Autopilot, fpl: IFFPL, inputs: dict=None) -> None:
        self.client = aircraft.client
        self.manifest = self.client.manifest.search("simulator")
        self.aircraft = aircraft
        self.autopilot = autopilot
        self.fpl = fpl
        self.reached_target = False
        self.current_spd = None
        self.current_acc = None
        self.target_acc = 9 * unit.mps2  # ~1.1 knot/s
        self._target_spd: Quantity = None
        self.flight_phase = FlightPhase.TAKE_OFF if aircraft.is_on_ground else fpl.next_wp(aircraft).flight_phase
        # setting inputs
        if inputs is None:
            print("Insert speed in knots or mach (<1)")
            self.inputs = {}
            if self.flight_phase == FlightPhase.TAKE_OFF:
                str_input = input("modify climb SPD? (y/n): ")
            else: str_input = "n"
            for attr in Spd:
                while True:
                    if str_input.lower() == "n" and attr in {Spd.clb_V1, Spd.clb_V2, Spd.clb_V3}:
                        break
                    if self.flight_phase != FlightPhase.TAKE_OFF and attr == Spd.Vr:
                        break
                    value = input(f"{attr.name}: ")
                    if attr == Spd.crz_V and (value == "" or "ci" in value.lower()):
                        self.inputs[attr] = value
                        break
                    if not value:
                        print(f"Must define {attr.name}")
                        continue
                    try:
                        v = float(value)
                        if v > 1:
                            self.inputs[attr] = v*unit.knot
                        else:
                            self.inputs[attr] = v*unit.mach
                        break
                    except ValueError:
                        print("Invalid input. Please enter a valid number.")
        else:
            self.inputs = inputs

        # setting Take Off parameters
        passed = False
        if self.flight_phase == FlightPhase.TAKE_OFF:
            self.TO_setting = 0.9
            if (Vr := self.inputs.get("Vr", "")):
                self.autopilot.Spd = Vr*unit.knot
            while not (Flex := input("Flex temp: ")):
                print("Invalid input")
            match Flex.split('-'):
                case (dto, temp):
                    dto = int(dto)
                    temp = int(temp)
                case (temp,) if temp.isdigit():
                    dto = 0
                    temp = int(temp)
                case _: passed = True
            if not passed:
                try:
                    k = self.aircraft.airplane.k
                    if temp >= self.aircraft.OAT:
                        self.TO_setting = ((100-dto*10) - k * (temp - self.aircraft.OAT)) / 100
                    elif temp <= 2:
                        self.TO_setting = (100 - temp * 10) / 100
                except (AttributeError, TypeError): ...
            logger.info(f"Take Off setting: {self.TO_setting:02f}")

        match self.flight_phase:
            case FlightPhase.TAKE_OFF:
                self.target_spd = self.inputs.get(Spd.Vr, 0*unit.knot)
            case FlightPhase.CLIMB:
                self.target_spd = self.inputs.get(Spd.clb_V1, 0*unit.knot)
            case FlightPhase.CRUISE:
                if (vt := self.inputs.get(Spd.crz_V, 0)) != 0:
                    self.target_spd = vt
            case FlightPhase.DESCENT:
                pass

    def __setattr__(self, name, value: Quantity):
        if not isinstance(value, Quantity):
            super().__setattr__(name, value)
            return
        if value.is_compatible_with(unit.knot):
            value = value.to(unit.ms)
        elif value.is_compatible_with(unit.mps2):
            value = value.to(unit.mps2)
        elif value.units == unit.mach:
            value = value.to(unit.mach)
        super().__setattr__(name, value)


    @property
    def Throttle(self) -> Quantity:
        value = self.aircraft.client.send_command("throttle", self.manifest)
        return round((1000 - value) / 2000, 2)*unit.no_unit
    
    @Throttle.setter
    def Throttle(self, value: Quantity) -> None:
        if isinstance(value, Quantity) and value.is_compatible_with(unit.no_unit):
            value = value.m
        elif isinstance(value, float):
            value = round(value, 2)
        else:
            raise ValueError("Invalid value")
        value = clip(value, 0, 1)
        value = int(value * -2000 + 1000)
        self.client.send_command("throttle", self.manifest, write=True, data=value)


    @property
    def target_spd(self) -> Quantity:
        return self._target_spd
    
    @target_spd.setter
    def target_spd(self, value: Quantity) -> None:
        if self.target_spd != value:
            self._target_spd = value
            self.autopilot.Spd = value
            self.reached_target = False
            self.autopilot.SpdOn = False
            logger.info(f"Target speed changed to {value.to(unit.knot) if value.units.is_compatible_with(unit.knot) else f"M{value.m: .2f}"}")

    def __call__(self) -> None:
        try:
            match self.flight_phase:
                case FlightPhase.TAKE_OFF:
                    self._take_off()
                case FlightPhase.CLIMB:
                    self._change_spd_climb()
                case FlightPhase.CRUISE:
                    self._change_spd_cruise()
                case FlightPhase.DESCENT:
                    self._change_spd_descend()
        except Exception:...
    def _change_spd_climb(self) -> None:
        spd_tol = 0.01 if self.autopilot.SpdMode else (3*unit.knot).to(unit.ms).m
        if self.autopilot.SpdMode:
            self.current_spd = self.aircraft.mach
            if not isclose(self.current_spd.m, self.target_spd.m, abs_tol=spd_tol) and not self.reached_target:
                delta_throttle = self.calc_delta_throttle()
                debug_logger.debug(f"Delta throttle: {delta_throttle}")
                
                if delta_throttle != 0 and not self.autopilot.SpdOn:
                    self.Throttle += delta_throttle
            else:
                if self.reached_target:
                    self.reached_target = True
                if not self.autopilot.SpdOn:
                    self.autopilot.SpdOn = True
        else:
            self.current_spd = self.aircraft.ias
            
            if not isclose(self.current_spd.m_as(unit.ms), self.target_spd.m_as(unit.ms), abs_tol=spd_tol) and not self.reached_target:
                delta_throttle = self.calc_delta_throttle()
                debug_logger.debug(f"Delta throttle: {delta_throttle}")
                if delta_throttle != 0 and not self.autopilot.SpdOn:
                    self.Throttle += delta_throttle
            else:
                self.reached_target = True
                if not self.autopilot.SpdOn:
                    self.autopilot.SpdOn = True

    def _change_spd_descend(self) -> None:
        self.current_spd = self.aircraft.mach if self.autopilot.SpdMode else self.aircraft.ias
        spd_tol = 0.01 if self.autopilot.SpdMode else (3*unit.knot).m_as(unit.ms)

        if self.Throttle <= 0 and self.current_acc >= 0:
            self.autopilot.Vs += 100  # Increase vertical speed to counter acceleration

        if not isclose(self.current_spd.m, self.target_spd.m, abs_tol=spd_tol) and not self.reached_target:
            delta_throttle = self.calc_delta_throttle()
            debug_logger.debug(f"Delta throttle: {delta_throttle}")
            if delta_throttle != 0 and not self.autopilot.SpdOn:
                self.Throttle += delta_throttle
        else:
            self.reached_target = True
            self.autopilot.SpdOn = True

    def _change_spd_cruise(self) -> None:
        # FIXME: add support for CI
        if isinstance(v_crz := self.inputs.get(Spd.crz_V), str):
            self.target_spd = self.fpl[self.aircraft.next_index].spd
        else:
            self.target_spd = v_crz
        ##
        if self.autopilot.SpdMode:
            spd_tol = 0.01
            self.current_spd = self.aircraft.mach
            if not isclose(self.current_spd.m, self.target_spd.m, abs_tol=spd_tol) and not self.reached_target:
                delta_throttle = self.calc_delta_throttle()
                debug_logger.debug(f"Delta throttle: {delta_throttle}")

                if delta_throttle != 0 and not self.autopilot.SpdOn:
                    self.Throttle += delta_throttle
            else:
                self.reached_target = True
                if not self.autopilot.SpdOn:
                    self.autopilot.SpdOn = True
        else:
            spd_tol = (3*unit.knot).m_as(unit.ms)
            self.current_spd = self.aircraft.ias
            if not isclose(self.current_spd.m_as(unit.ms), self.target_spd.m_as(unit.ms), abs_tol=spd_tol) and not self.reached_target:
                delta_throttle = self.calc_delta_throttle()
                debug_logger.debug(f"Delta throttle: {delta_throttle}")
                if delta_throttle != 0 and not self.autopilot.SpdOn:
                    self.Throttle += delta_throttle
            else:
                self.reached_target = True
                if not self.autopilot.SpdOn:
                    self.autopilot.SpdOn = True

    def _take_off(self) -> None:
        if self.aircraft.n1 < 0.5*unit.no_unit or (not self.aircraft.is_on_runway and self.aircraft.is_on_ground):
            sleep(1)
            return
        self.Throttle = self.TO_setting
        logger.info(f"Starting takeoff\nTO n1:{self.aircraft.n1_target:.2f}")
        if self.aircraft.is_on_ground or (self.aircraft.agl < 50*unit.ft and self.aircraft.vs < 0*unit.fpm): 
            sleep(1)
            return
        debug_logger.debug("Takeoff")
        if not self.aircraft.landing_gear_status:
            debug_logger.debug("Landing gear is up")
            return
        debug_logger.debug("Landing gear is down, trying to retract")
        self.target_spd = self.aircraft.airplane.climb_v1
        sleep(0.2)
        self.aircraft.Landing_gear_toggle
        del self.TO_setting



    def calc_delta_throttle(self) -> Quantity:
        self.current_acc = self.aircraft.accel * -1e3
        if isclose(self.current_acc.m, self.target_acc.m, abs_tol=5e-1, rel_tol=5e-2):
            return 0

        delta_spd = self.target_spd - self.current_spd
        delta_acc = sign(delta_spd)*(self.target_acc - self.current_acc).m
        debug_logger.debug(f"Delta acc: {delta_acc}")

        delta = sign(delta_acc) * (0.05 if abs(delta_acc) > abs(self.target_acc.m*.5) else 0.01)
        debug_logger.debug(f"Delta: {delta_acc}")
        debug_logger.debug(f"delta_throttle: {delta}")
        return delta
