from module.aircraft import Aircraft, Autopilot
from module.FlightPlan import IFFPL
from module.client import retrive_ip_port, IFClient
from module.logger import logger, debug_logger
from flight_phases import climbing, cruise, takeoff
from atexit import register
from module import FlightPlan
import json
import matplotlib.pyplot as plt #remove later

import matplotlib.pyplot as plt

def plot_fpl(fpl, ratios, threshold):

    yaltitude = []
    xaxis = []
    colors = []  # List to store colors for each ratio point
    tot_dist = 0

    for FIX_point in fpl:
        tot_dist += FIX_point.dist_to_prev
        if FIX_point.get_altitude() != -1:
            xaxis.append(tot_dist)
            yaltitude.append(FIX_point.get_altitude())
            
            # Assign color based on fly_phase
            if FIX_point.fly_phase == 0:
                colors.append('b')
            elif FIX_point.fly_phase == 1:
                colors.append('green')
            elif FIX_point.fly_phase == 2:
                colors.append('b')
            else:
                colors.append('black')  # Other phases are blue

    # Create a figure and axes
    fig, ax = plt.subplots(2, 1, figsize=(10, 10))  # 2 rows, 1 column

    ythreshold = [threshold] * len(ratios)  # Create a list with the same length as ratios

    # Plot the first dataset as a scatter plot
    ax[0].scatter(xaxis, ratios, color=colors, marker='+')
    ax[0].plot(xaxis, ythreshold, linestyle="--", color='r')
    ax[0].set_ylabel('altitude/distance ratio')
    ax[0].grid()

    # Plot the second dataset
    ax[1].plot(xaxis, yaltitude, marker='o', linestyle='-', color='b')
    ax[1].set_ylabel('altitude [m]')
    ax[1].grid()

    # Adjust layout
    plt.tight_layout()

    # Display the plots
    plt.show()




def main_loop() -> None:
    aircraft: Aircraft = Aircraft(ip, port)
    fpl = IFFPL(aircraft.send_command("full_info"))
    # modifca piano volo dividendo in climb cruise e descent
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

        register(lambda: debug_logger.info(f"n_commands {Aircraft.command_sent}, {Aircraft.total_call_time/1e9:.2f} seconds"))
        #main_loop()

        ip, port = retrive_ip_port()
        client = IFClient(ip, port)
        fpl_analyzed, ratios, threshold = FlightPlan.add_flightPhase_to_fpl(client.send_command('full_info')) # fpl_analyzed is a deque of FIX points

        # with open("fpl.json", "r") as json_data_file:
        # json_data = json.load(json_data_file)
        # fpl_analyzed = FlightPlan.create_fpl(json_data)

        plot_fpl(fpl_analyzed, ratios, threshold)