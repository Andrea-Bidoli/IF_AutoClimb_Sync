from numpy import sqrt
from pint import UnitRegistry, Quantity

class PintUnitManager:
    _instance = None
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PintUnitManager, cls).__new__(cls)
            cls.__init_unit__(cls._instance)
        return cls._instance

    def __init_unit__(self):
        self.ureg: UnitRegistry = UnitRegistry()
        self.ureg.define("meter_per_minute = meter / minute = m/min")

        # Define common units for easier access
        self.unit = self.ureg
        self.ms = self.ureg.meter / self.ureg.second
        self.knot = self.ureg.knot
        self.km = self.ureg.kilometer
        self.m = self.ureg.meter
        self.ft = self.ureg.foot
        self.nm = self.ureg.nautical_mile
        self.mph = self.ureg.mile / self.ureg.hour
        self.kph = self.ureg.kilometer / self.ureg.hour
        self.fpm = self.ureg.foot / self.ureg.minute
        self.mpm = self.ureg("m/min")
        self.mach = self.ureg.dimensionless
        self.rad = self.ureg.radian
        self.deg = self.ureg.degree
        self.rpm = self.ureg.rpm
        self.percent = self.ureg.percent

def mach2tas_SI(mach: float, alt: float) -> float:
    T0 = 288.15
    gamma = 1.4
    R = 287.05
    L = 0.0065
    T = T0 - L * alt
    a = sqrt(gamma * R * T)
    return mach * a

def tas2mach_SI(tas: float, alt: float) -> float:
    T0 = 288.15
    gamma = 1.4
    R = 287.05
    L = 0.0065
    T = T0 - L * alt
    a = sqrt(gamma * R * T)
    return tas / a

def tas2mach_Aero(tas: float, alt: float) -> float:
    alt *= 0.3048
    tas /= 1.994
    return tas2mach_SI(tas, alt)

def mach2tas_Aero(mach: float, alt: float) -> float:
    alt = alt * 0.3048
    return mach2tas_SI(mach, alt) * 1.94384


def ias2tas_SI(ias: float, alt: float) -> float:
    return ias / sqrt(density(alt) / 1.225)


def ias2tas_Aero(ias: float, alt: float) -> float:
    ias = ias * 0.514444
    alt = alt * 0.3048
    return ias2tas_SI(ias, alt) * 1.94384


def density(z: float) -> float:
    rho_0 = 1.225
    T0 = 288.15
    g = 9.80665
    R = 287.05
    L = 0.0065

    T = T0 - L * z
    return rho_0 * (T / T0) ** (g / (R * L) - 1)

def decimal_to_dms(decimal: float) -> str:
    degrees = int(decimal)
    minutes = int((decimal - degrees) * 60)
    seconds = ((decimal - degrees) * 60 - minutes) * 60
    return f"{degrees}° {minutes}' {seconds:.2f}\""