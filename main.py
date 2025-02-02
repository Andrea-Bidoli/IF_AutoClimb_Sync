from module.flight_phases import vnav, takeoff, Only_Authothrottle
from module import Aircraft, Autopilot, logger, debug_logger, retrive_ip_port, IFFPL, retrive_airplane
from atexit import register
from tabulate import tabulate

ip, port = retrive_ip_port()


def main_loop() -> None:
    aircraft: Aircraft = Aircraft(ip, port)
    fpl = IFFPL(aircraft.send_command("full_info"), write=True)
    autopilot: Autopilot = Autopilot(ip, port)
    debug_logger.debug("Aircraft and Autopilot initialized")
    
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
    
    takeoff(aircraft, autopilot)
    if not only_AT:
        vnav(aircraft, autopilot, fpl)
    else:
        Only_Authothrottle(aircraft, autopilot, fpl)

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
