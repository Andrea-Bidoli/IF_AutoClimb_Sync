def_username = "AndreaBidoli"
def_user_id = 913215
create_request_str_id = lambda user_id: f"https://www.simbrief.com/api/xml.fetcher.php?userid={user_id}&json=1"
create_request_str_username = lambda username: f"https://www.simbrief.com/api/xml.fetcher.php?username={username}&json=1"


request_str_usernames = create_request_str_username(def_username)
request_str_user_id = create_request_str_id(def_user_id)

type JsonType = str | dict | list | int | float | bool | None

from .navlog import Navlog, Simbrief_Airport
from .tlr import Tlr


class Simbrief_FPL:
    def __init__(self, data: JsonType):
        self.origin = Simbrief_Airport(**data.get('origin'))
        self.destination = Simbrief_Airport(**data.get('destination'))
        self.navlog: Navlog = Navlog(data)
        self.tlr: Tlr = Tlr(data)