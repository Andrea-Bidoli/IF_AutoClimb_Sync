from module.aircraft import Aircraft, Autopilot
from module.FlightPlan import IFFPL
from module.client import retrive_ip_port
from module.logger import logger, debug_logger
from flight_phases import climbing, cruise, takeoff
from atexit import register


ip, port = retrive_ip_port()


def main_loop() -> None:
    aircraft: Aircraft = Aircraft(ip, port)
    fpl = IFFPL(aircraft.send_command("full_info"))
    autopilot: Autopilot = Autopilot(ip, port)
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
    except Exception:
        debug_logger.error("", exc_info=True)
