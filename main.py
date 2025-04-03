from module.flight_phases import Vnav, Lnav, takeoff, Only_Authothrottle
from module import IFClient, Aircraft, Autopilot, IFFPL, logger, retrive_ip_port
from module import Autothrottle
from tabulate import tabulate

ip, port = retrive_ip_port()


def main_loop() -> None:
    match input("Only AT? (y/n): ")[:1]:
        case "y":
            only_AT = True
        case "n":
            only_AT = False
        case _:
            logger.error("Invalid input, only AT will be used")
            only_AT = True


    client: IFClient = IFClient(ip, port)
    aircraft: Aircraft = Aircraft(client)
    if not only_AT:
        fpl: IFFPL = IFFPL.from_str(client.send_command("full_info"), write=True)
    autopilot: Autopilot = Autopilot(client)
    autothrottle = Autothrottle(aircraft, autopilot, fpl)
    vnav: Vnav = Vnav(aircraft, autopilot, autothrottle, fpl)
    logger.info("Aircraft, Autopilot, Vnav initialized")
    only_AT = False

    if aircraft.airplane is not None:
        data = list(zip(*list((vars(aircraft.airplane).items()))))
        logger.info("\n"+tabulate(data, headers="firstrow"))

    if not only_AT:
        while vnav(): continue
    else:
        Only_Authothrottle(aircraft, autopilot)

    logger.info("Autopilot finished")
    if aircraft.airplane is not None:
        logger.info("\n"+tabulate(data, headers="firstrow"))


if __name__ == "__main__":
    # try:
        logger.info("Starting main loop")
        main_loop()
    # except Exception:
        # debug_logger.error("", exc_info=True)
