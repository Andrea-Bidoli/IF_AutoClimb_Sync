from flight_phases import vnav, takeoff, climbing_test
from module import Aircraft, Autopilot, logger, debug_logger, retrive_ip_port, IFFPL, init_loggers
from atexit import register

init_loggers(debug=False)
ip, port = retrive_ip_port()


def main_loop() -> None:
    aircraft: Aircraft = Aircraft(ip, port)
    fpl = IFFPL(aircraft.send_command("full_info"), write=True)
    autopilot: Autopilot = Autopilot(ip, port)
    debug_logger.debug("Aircraft and Autopilot initialized")
    takeoff(aircraft, autopilot)
    vnav(aircraft, autopilot, fpl)
    # climbing_test(aircraft, autopilot)
    logger.info("Autopilot finished")


if __name__ == "__main__":
    # try:
        register(lambda: debug_logger.info(f"n_commands {Aircraft.command_sent}, {Aircraft.total_call_time/1e9:.2f} seconds"))
        main_loop()
    # except Exception:
        # debug_logger.error("", exc_info=True)
