from module.flight_phases import vnav, takeoff, climbing_test
from module import Aircraft, Autopilot, logger, debug_logger, retrive_ip_port, IFFPL, Airplane
from atexit import register
from tabulate import tabulate

ip, port = retrive_ip_port()


def main_loop() -> None:
    aircraft: Aircraft = Aircraft(ip, port)
    fpl = IFFPL(aircraft.send_command("full_info"), write=True)
    autopilot: Autopilot = Autopilot(ip, port)
    debug_logger.debug("Aircraft and Autopilot initialized")
    takeoff(aircraft, autopilot)
    # if fpl is not None:
    vnav(aircraft, autopilot, fpl)
    # else:
    # climbing_test(aircraft, autopilot, fpl)
    logger.info("Autopilot finished")


if __name__ == "__main__":
    # try:
        tab_headers = ("n_commands", "total_call_time [s]")
        register(lambda: debug_logger.info("\n"+tabulate([[Aircraft.command_sent, round(Aircraft.total_call_time/1e9, 2)],], headers=tab_headers)))
        main_loop()
    # except Exception:
        # debug_logger.error("", exc_info=True)
