from GUI_utilities import SSN_Server_UI
from MQTT import MQTT
import time


server_end = ('192.168.0.120', 9999)
node_end = ('', 8888)
CURRENT_SENSOR_RATINGS = ['NONE', 5, 10, 15, 20, 25, 30, 50, 60, 100, 250]
SSN_DEFAULT_CONFIGS = [9, 90, 10, 9, 95, 6, 6, 27, 2, 6, 28, 3, 1]


def main():
    main_gui = SSN_Server_UI(window_theme="aquativo", window_title="SSN Server Simulator", window_geometry='945x735+610+120')
    main_gui.setup_input_interface(current_sensor_ratings=CURRENT_SENSOR_RATINGS, mac_addresses_filename="MAC_utilities/MAC.txt", default_configs=SSN_DEFAULT_CONFIGS)
    main_gui.setup_buttons()
    main_gui.setup_incoming_data_interface(NumOfNodes=2)
    # main_gui.setup_serial_communication(serial_port='COM29', baudrate=19200, log_file='serial_log.txt')
    # main_gui.setup_udp_communication(server_end=server_end)
    main_gui.setup_mqtt_communication(client_id="SSNSuperUser", host="192.168.0.120")
    # main_gui.setup_csv_data_recording(csv_file="recording/recording.csv")
    # start the main loop
    main_gui.start()
    pass


def test():
    mqtt_obj = MQTT(client_id="SSNSuperUser", host="192.168.0.120")
    mqtt_obj.client.loop_start()
    while True:
        print("Waiting for 1 second")
        time.sleep(1)
        pass
    pass


if __name__ == "__main__":
    main()
    pass
