from numpy import sqrt, sign
from . import in_range

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .aircraft import Aircraft

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


def knot2ms(knot: float) -> float:
    return knot / 1.944


def ms2knot(ms: float) -> float:
    return int(ms * 1.944)


def ft2m(ft: float) -> float:
    return ft * 0.3048


def m2ft(m: float) -> float:
    return m / 0.3048


def ms2fpm(ms: float) -> float:
    return ms * 196.85


def fpm2ms(fpm: float) -> float:
    return fpm / 196.85


def calc_delta_throttle(current: float, target: float, aircraft: 'Aircraft') -> float:
    """Calculate the delta throttle to maintain the acc target

    Args:
        current (float): current value
        target (float): target value
        aircraft (Aircraft): aircraft object

    Returns:
        float: delta throttle to add
    """
    if in_range(current, target, 0.2):
        delta = 0
    else:
        delta = round(target - current, 2)
    if aircraft.n1_target >= 0.9 or delta == 0:
        return 0
    elif abs(delta) > 0.1 and aircraft.n1_target <= 0.8:
        return sign(delta) * 0.1
    else:
        return sign(delta) * 0.01


def decimal_to_dms(decimal: float) -> str:
    degrees = int(decimal)
    minutes = int((decimal - degrees) * 60)
    seconds = ((decimal - degrees) * 60 - minutes) * 60
    return f"{degrees}° {minutes}' {seconds:.2f}\""