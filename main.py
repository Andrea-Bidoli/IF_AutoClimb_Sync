from module.aircraft import Aircraft, Autopilot
from module.FlightPlan import IFFPL
from module.client import retrive_ip_port
from module.logger import logger, debug_logger
from flight_phases import climbing, cruise, takeoff
from atexit import register

from time import perf_counter

t_init = perf_counter()
ip, port = retrive_ip_port()

def main_loop() -> None:
    fpl = IFFPL(aircraft.send_command("full_info"))
    autopilot: Autopilot = Autopilot(ip, port)
    flex_temp = int(input("Flex temperature: "))
    try:
        takeoff(aircraft, autopilot, flex_temp)
    except ValueError:
        logger.warning("Aircraft don't support FLEX TEMP, please take off manually")
    logger.info("Starting climb")
    climbing(aircraft, autopilot, fpl)
    logger.info("Starting cruise")
    cruise(aircraft, autopilot, fpl)
    logger.info("Autopilot finished")

if __name__ == "__main__":
    try:
        aircraft: Aircraft = Aircraft(ip, port)
        register(lambda : debug_logger.info(f"n_commands {aircraft.command_sent}, {aircraft.total_call_time:.2f} seconds"))
        main_loop()
    except KeyboardInterrupt:...