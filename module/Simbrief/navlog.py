from . import *
from .. import unit
from ..FlightPlan import FlightPhase


class Fix: ...

class Simbrief_Fix(Fix):
    def __init__(self, **kwargs):
        # names
        self.name = kwargs.get('name')
        self.ident = kwargs.get('ident')
        # stage of flight
        stage = kwargs.get('stage')
        match stage:
            case 'CLB':
                self.stage = FlightPhase.CLIMB
            case 'CRZ':
                self.stage = FlightPhase.CRUISE
            case 'DSC':
                self.stage = FlightPhase.DESCENT
        # altitudes msl
        self.alt = int(kwargs.get('altitude_feet'))*unit.ft
        # speeds
        self.ias = int(kwargs.get('ind_airspeed'))*unit.knot
        self.mach = float(kwargs.get('mach'))*unit.mach
        self.distance = float(kwargs.get('distance'))*unit.nm
    
    # def __repr__(self):
    #     return f"{self.ident}:\n{self.stage=} {self.ias=} {self.mach=}\n{self.alt=}"

class Simbrief_Airport(Fix):
    def __init__(self, **kwargs):
        # names
        self.name = kwargs.get('icao_code')
        self.plan_rwy = kwargs.get('plan_rwy')

class Navlog(list[Simbrief_Airport | Simbrief_Fix]):
    def __init__(self, data: JsonType):
        # data -> intero json file/string from simbrief API response
        data_ = data.get('navlog')
        if data_ is None:
            return
        fixes = data_.get('fix')
        # creare una lista di oggetti Simbrief_Fix
        for json_fix in fixes:
            self.append(Simbrief_Fix(**json_fix))