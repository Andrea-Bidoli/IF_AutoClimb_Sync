from . import *
from .. import unit

class Takeoff:
    def __init__(self, data: JsonType):
        self.data_ = data.get('takeoff')
        self.planned_rwy = self.data_.get('conditions', {}).get('planned_runway')
        rwy_data = filter(lambda x: x.get('identifier') == self.planned_rwy, self.data_.get('runway'))
        rwy_data = next(rwy_data)
        self.hdg = int(rwy_data.get('magnetic_course'))*unit.deg
        self.flap_setting = rwy_data.get('flap_setting')
        self.flex_temp = int(rwy_data.get('flex_temperature'))
        self.thrust_setting = rwy_data.get('thrust_setting')

        self.vr = int(rwy_data.get('speeds_vr'))*unit.knot
        
class Landing:
    def __init__(self, data: JsonType):
        self.data_ = data.get('landing')
        self.planned_rwy = self.data_.get("conditions", {}).get('planned_runway')
        self.vref = int(self.data_.get('distance_dry', {}).get("speeds_vref"))*unit.knot
        self.flap_setting = self.data_.get('distance_dry', {}).get("flap_setting")

class Tlr:
    def __init__(self, data: JsonType):
        self.data = data.get('tlr')
        if self.data == {} or self.data is None:
            return
        self.takeoff = Takeoff(self.data)
        self.landing = Landing(self.data)
        del self.data