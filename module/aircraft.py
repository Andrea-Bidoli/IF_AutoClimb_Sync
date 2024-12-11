from .database import Airplane, retrive_airplane
from numpy import radians, array, arcsin
from .logger import debug_logger
from numpy.linalg import norm
from .client import IFClient

class Aircraft(IFClient):
    def __init__(self, ip: str, port: int) -> None:
        super().__init__(ip, port)
        tmp = self.send_command("aircraft/0/name")
        tmp = id_2_icao.get(tmp, "0xdd")
        self.airplane: Airplane = retrive_airplane(tmp)
        if self.airplane is None:
            debug_logger.warning(f"Airplane {self.send_command('aircraft/0/name')} not found in database")
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
    def next_name(self) -> str:
        return self.send_command("flightplan", "next_waypoint_name")
    @property
    def next_index(self) -> int:
        return self.send_command("flightplan", "next_waypoint_index")
    @property
    def dist_to_next(self) -> float:
        return self.send_command("flightplan", "next_waypoint_dist")*1852
    @property
    def dist_to_dest(self) -> float:
        return self.send_command("flightplan", "destination_dist")*1852

    @property
    def accel(self) -> float:
        x = self.send_command("acceleration", "x")
        y = self.send_command("acceleration", "y")
        z = self.send_command("acceleration", "z")
        return norm(array([x, y, z]))
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
    def elevator(self) -> int:
        return self.send_command(2, 1, 'axes')
    @elevator.setter
    def elevator(self, value: int) -> None:
        value = max(-1000, min(value, 1000))
        self.send_command(2, 1, 'axes', write=True, data=value)

    @property
    def α(self) -> float:
        return arcsin(self.vs/self.tas)
    @property
    def γ(self) -> float:
        """positive angle (wind left to right)

        Returns:
            float: slipstream angle
        """
        crosswind = self.send_command("crosswind_component")
        return arcsin(crosswind/self.tas)

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
        value = self.send_command("simulator","throttle")
        return round((1000-value) / 2000, 2)

    @Alt.setter
    def Alt(self, value: float) -> None:
        self.send_command("alt", "target", write=True, data=value)
    @Vs.setter
    def Vs(self, value: float) -> None:
        self.send_command("vs", "target", write=True, data=value*60)
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
        self.send_command("simulator","throttle", write=True, data=value)
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

id_2_icao = {
    "Airbus A220-300": "BCS3",
    "Airbus A319": "A319",
    "Airbus A320": "A320",
    "Airbus A321": "A321",
    "Airbus A330 - 300": "A333",
    "Airbus A330 - 900": "A339",
    "Airbus A350": "A359",
    "Airbus A380": "A388",
    "Boeing 737-700": "B737",
    "Boeing 737-800": "B738",
    "Boeing 737-900": "B739",
    "Boeing 747-200": "B742",
    "Boeing 747-400": "B744",
    "Boeing 747-8": "B748",
    "Boeing 757-200": "B752",
    "Boeing 777-200ER": "B772",
    "Boeing 777-200LR": "B77L",
    "Boeing 777-300ER": "B77W",
    "Boeing 777F": "B77F",
    "Boeing 787-8": "B788",
    "Boeing 787-9": "B789",
    "Boeing 787-10": "B78X",
    "Bombardier CRJ-200": "CRJ2",
    "Bombardier CRJ-700": "CRJ7",
    "Bombardier CRJ-900": "CRJ9",
    "Bombardier CRJ-1000": "CRJX",
    "Embraer E175": "E175",
    "Embraer E190": "E190",
    "McDonnell Douglas MD-11": "MD11",
}
