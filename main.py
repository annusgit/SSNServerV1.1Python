
from GUI_utilities.SSN_Server_GUI import SSN_Server_UI

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
    main_gui.setup_udp_communication(server_end=server_end)
    main_gui.setup_csv_data_recording(csv_file="recording/recording.csv")
    # start the main loop
    main_gui.start()
    pass


if __name__ == "__main__":
    main()
    # generate_all_MAC_from_range(file_name="MAC.txt")
    # import utils.utils as ut
    # ut.calc_half_wave_RMS()
    # import sys, time, datetime
    # while True:
    #     original = int(round(time.time()))
    #     bytes = ut.get_bytes_from_int(original)
    #     this_time = ut.get_int_from_bytes(highest_byte=bytes[0], higher_byte=bytes[1], high_byte=bytes[2], low_byte=bytes[3])
    #     good_time = datetime.datetime(1, 1, 1) + datetime.timedelta(seconds=this_time)
    #     # print("Your time is: {}/{}, Data type is: {}, It occupies {} bits".format(original, this_time, type(this_time), sys.getsizeof(this_time)))
    #     print("Your time is: {}:{}:{} {}/{}/{}".format(good_time.hour, good_time.minute, good_time.second, good_time.day, good_time.month, 1969+good_time.year))
    #     time.sleep(1)
    pass
