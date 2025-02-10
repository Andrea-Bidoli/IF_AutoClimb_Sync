from module.flight_phases import Vnav, Lnav, takeoff, Only_Authothrottle, Spd
from module import Aircraft, Autopilot, logger, debug_logger, retrive_ip_port, IFFPL
from module import Autothrottle
from module import Quantity, unit
from typing import Literal
from atexit import register
from tabulate import tabulate

ip, port = retrive_ip_port()


def input_data() -> dict[int, Quantity]:
    inputs = {}
    for attr in Spd:
        while True:
            value = input(f"Enter value for {attr.name}(in kts or mach number if cruise above 28000ft): ")
            if value == "":
                inputs[attr] = -1*unit.dimensionless
                break
            try:
                inputs[attr] = float(value)*unit.knot
                break
            except ValueError:
                print("Invalid input. Please enter a valid number.")
    return inputs

    
def mainloop() -> None:
    input_dict = input_data()    
    aircraft: Aircraft = Aircraft(ip, port)
    autopilot: Autopilot = Autopilot(ip, port)
    fpl: IFFPL = IFFPL(aircraft.send_command("full_info"), write=True)
    autothrottle: Autothrottle = Autothrottle(aircraft, autopilot, fpl)
    vnav: Vnav = Vnav(aircraft, autopilot, fpl, autothrottle, input_dict)
    # lnav: Lnav = Lnav(aircraft, autopilot, fpl)
    
    while True:
        vnav()



def main_loop() -> None:
    aircraft: Aircraft = Aircraft(ip, port)
    fpl: IFFPL = IFFPL(aircraft.send_command("full_info"), write=True)
    autopilot: Autopilot = Autopilot(ip, port)
    debug_logger.debug("Aircraft and Autopilot initialized")
    vnav: Vnav = Vnav(aircraft, autopilot, fpl, inputs)
    only_AT = False
    match input("Only AT? (y/n): ")[:1]:
        case "y":
            only_AT = True
        case "n":
            only_AT = False
        case _:
            logger.error("Invalid input, only AT will be used")
            only_AT = True
    if aircraft.airplane is not None:
        data = list(zip(*list((vars(aircraft.airplane).items()))))
        logger.info("\n"+tabulate(data, headers="firstrow"))
    
        inputs = {
        Spd.Vr: input("Vr: ") or "",
        Spd.clb_V1: input("clb V1: ") or "",
        Spd.clb_V2: input("clb V2: ") or "",
        Spd.clb_V3: input("clb V3: ") or "",
        Spd.crz_V: input("crz V: ") or "",
    }
    
    takeoff(aircraft, autopilot, inputs)
    if not only_AT:
        vnav(aircraft, autopilot, fpl, inputs)
    else:
        Only_Authothrottle(aircraft, autopilot, inputs)

    logger.info("Autopilot finished")
    if aircraft.airplane is not None:
        logger.info("\n"+tabulate(data, headers="firstrow"))

if __name__ == "__main__":
    # try:
        tab_headers = ("n_commands", "total_call_time [s]")
        register(lambda: debug_logger.info("\n"+tabulate([[Aircraft.command_sent, round(Aircraft.total_call_time/1e9, 2)],], headers=tab_headers)))
        main_loop()
    # except Exception:
        # debug_logger.error("", exc_info=True)
