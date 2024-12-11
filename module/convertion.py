from numpy import sqrt


def mach2tas_SI(mach: float, alt: float) -> float:
    T0 = 288.15
    gamma = 1.4
    R = 287.05
    L = 0.0065
    T = T0 - L * alt
    a = sqrt(gamma * R * T)
    return mach * a


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
    return ms * 1.944


def ft2m(ft: float) -> float:
    return ft * 0.3048


def m2ft(m: float) -> float:
    return m / 0.3048


def ms2fpm(ms: float) -> float:
    return ms * 196.85


def fpm2ms(fpm: float) -> float:
    return fpm / 196.85
