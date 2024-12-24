from module.aircraft import Aircraft, Autopilot
from module.FlightPlan import IFFPL
from module.client import retrive_ip_port, IFClient
from module.logger import logger, debug_logger
from flight_phases import climbing, cruise, takeoff
from atexit import register
from module import FlightPlan
import json
import matplotlib.pyplot as plt #remove later

# ip, port = retrive_ip_port()

def plot_list_colors(data):
# Unzip the data into two lists: colors and values
        colors, values = zip(*data)

        # Create a figure
        plt.figure(figsize=(10, 5))

        # Create a scatter plot
        plt.scatter(range(len(values)), values, color=colors, s=100)  # s is the size of the points

        # Add title and labels
        plt.title('Scatter Plot with Color-Coded Points')
        plt.xlabel('Index')
        plt.ylabel('Value')

        # Show grid
        plt.grid()

def plot_data(xaxis, data1, data2, avg):
    # Create a figure and axes
    fig, ax = plt.subplots(2, 1, figsize=(10, 10))  # 2 rows, 1 column

    avg_list = []
    for i in range(len(xaxis)):
        avg_list.append(avg)

    # Plot the first dataset
    ax[0].plot(xaxis, data1, marker='o', linestyle='-', color='b')
    ax[0].set_ylabel('altitude/distance ratio')
    ax[0].plot(xaxis, avg_list, linestyle="--", color='r')
    ax[0].grid()

    # Plot the second dataset
    ax[1].plot(xaxis, data2, marker='+', linestyle='-', color='g')
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
    try:
        register(lambda: debug_logger.info(f"n_commands {Aircraft.command_sent}, {Aircraft.total_call_time/1e9:.2f} seconds"))
        #main_loop()

        ip, port = retrive_ip_port()
        client = IFClient(ip, port)
        fpl_analyzed = FlightPlan.create_fpl(client.send_command('full_info'))

        # with open("fpl.json", "r") as json_data_file:
        # json_data = json.load(json_data_file)
        # fpl_analyzed = FlightPlan.create_fpl(json_data)
       
        avg_ratio_3 = sum(fpl_analyzed[1])/(3 * len(fpl_analyzed[1]))

        plot_data(fpl_analyzed[0], fpl_analyzed[1], fpl_analyzed[2], avg_ratio_3)
        
        print("Media ratio:", avg_ratio_3)
        plt.show()

        
    except KeyboardInterrupt:
        ...
    except Exception:
        debug_logger.error("", exc_info=True)
