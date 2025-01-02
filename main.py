from flight_phases import climbing, cruise, takeoff
from module.aircraft import Aircraft, Autopilot
from module.logger import logger, debug_logger
from module.client import retrive_ip_port
from module.FlightPlan import IFFPL
from atexit import register


ip, port = retrive_ip_port()

debug = True


if debug:
    debug_logger.Toggle_Stream()


def main_loop() -> None:
    aircraft: Aircraft = Aircraft(ip, port)
    fpl = IFFPL(aircraft.send_command("full_info"), write=True)
    autopilot: Autopilot = Autopilot(ip, port)
    debug_logger.debug("Aircraft and Autopilot initialized")
    debug_logger.debug(f"Altitude: {aircraft.msl}, Ground Speed: {aircraft.gs}")
    try:
        takeoff(aircraft, autopilot)
    except ValueError:
        logger.warning("Aircraft don't support FLEX TEMP, please take off manually")
    logger.info("Starting climb")
    climbing(aircraft, autopilot, fpl)
    logger.info("Starting cruise")
    cruise(aircraft, autopilot, fpl)
    logger.info("Autopilot finished")


if __name__ == "__main__":
    try:
        register(lambda: debug_logger.info(f"n_commands {Aircraft.command_sent}, {Aircraft.total_call_time/1e9:.2f} seconds"))
        main_loop()
    except KeyboardInterrupt:
        ...
    # except Exception:
    #     debug_logger.error("", exc_info=True)
