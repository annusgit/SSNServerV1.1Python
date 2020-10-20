import csv
import time
import datetime
from tkinter import *  # Normal Tkinter.* widgets are not themed!
from ttkthemes import ThemedTk, ThemedStyle
from tkinter import ttk
# from MQTT.mqtt import *
from UDP_COMM.udp_communication import *
# from SERIAL_COMM.serial_communication import *
from MAC_utilities.MAC_utils import get_MAC_addresses_from_file
# -----------------------------------------------------IMPORTS FROM MQTT.py
import paho.mqtt.client as mqtt
import time
import utils.utils as utils
from MAC_utilities.MAC_utils import get_mac_bytes_from_mac_string

# -------------------------------------------------------------------------

vertical_spacing = 21
horizontal_spacing = 120
Machine_State_ID_to_State = {0: 'OFF', 1: 'IDLE', 2: 'ON'}
countforTCOMMFAIL, countforTREADFAIL = 0, 0

# -----------------------------------------------------IMPORTS FROM MQTT.py
SSN_MessageType_to_ID = {
    'GET_MAC': 1,
    'SET_MAC': 2,
    'GET_TIMEOFDAY': 3,
    'SET_TIMEOFDAY': 4,
    'GET_CONFIG': 5,
    'SET_CONFIG': 6,
    'ACK_CONFIG': 7,
    'STATUS_UPDATE': 8,
    'RESET_MACHINE_TIME': 9,
    'DEBUG_EEPROM_CLEAR': 10,
    'DEBUG_RESET_SSN': 11
}
SSN_MessageID_to_Type = {x: y for y, x in SSN_MessageType_to_ID.items()}
SSN_ActivityLevelID_to_Type = {0: 'NORMAL', 1: 'ABNORMAL', 2: 'TREADFAIL', 3: 'TCOMMFAIL'}
offset = 12
broker_ip = '192.168.0.110'

##-------------------------------------------------------------------------

class SSN_Button_Widget:
    def __init__(self, window, button_text, button_command, button_pos):
        self.this_button = ttk.Button(window, text=button_text, command=button_command)  # bg="white", fg="blue"
        self.this_button.place(x=button_pos[0], y=button_pos[1])
        pass

    def config(self, **kwargs):
        self.this_button.config(**kwargs)


class SSN_Radio_Button_Common_Option_Widget:
    def __init__(self, window):
        self.option = StringVar()
        self.window = window
        self.radio_buttons = list()
        pass

    def add_radio(self, radio_text, radio_value, radio_pos):
        self.radio_buttons.append(ttk.Radiobutton(self.window, text=radio_text, value=radio_value, var=self.option))
        self.radio_buttons[-1].place(x=radio_pos[0], y=radio_pos[1])
        pass

    def getSelectedNode(self):
        return int(self.option.get())


class SSN_Text_Entry_Widget:
    def __init__(self, window, label_text, label_pos, text_entry_width, text_pos, default_value='100',
                 justification='center'):
        self.this_label = ttk.Label(window, text=label_text)
        self.this_label.place(x=label_pos[0], y=label_pos[1])
        self.this_text_entry = ttk.Entry(window, width=text_entry_width)
        self.this_text_entry.insert(END, default_value)
        self.this_text_entry.config(justify=justification)
        self.this_text_entry.place(x=text_pos[0], y=text_pos[1])
        pass

    def update(self, this_update):
        self.update = this_update
        pass

    def get(self):
        return self.this_text_entry.get()


class SSN_Text_Display_Widget:
    def __init__(self, window, label_text, label_pos, text_size, text_pos, color='black'):
        self.this_label = ttk.Label(window, text=label_text)
        self.this_label.place(x=label_pos[0], y=label_pos[1])
        self.this_text = Text(window, fg=color)
        self.this_text.place(x=text_pos[0], y=text_pos[1], width=text_size[0], height=text_size[1])
        pass

    def update(self, new_text_string, justification='center'):
        self.this_text.delete('1.0', END)
        self.this_text.insert(END, new_text_string)
        self.this_text.tag_configure('tag', justify=justification)
        self.this_text.tag_add('tag', 1.0, 'end')
        pass

    def change_text_color(self, new_color):
        self.this_text.config(fg=new_color)

    def clear(self):
        self.this_text.delete('1.0', END)


class SSN_Dual_Text_Display_Widget(SSN_Text_Display_Widget):
    def __init__(self, window, label_text, label_pos, text_size, text_pos1, text_pos2, color='black',
                 justification='center'):
        super().__init__(window, label_text, label_pos, text_size, text_pos1, color)
        self.that_text = Text(window, fg=color)
        self.that_text.tag_configure('sometag', justify=justification)
        self.that_text.tag_add('sometag', 1.0, 'end')
        self.that_text.place(x=text_pos2[0], y=text_pos2[1], width=text_size[0], height=text_size[1])

    def update(self, new_text_strings, justification='center'):
        super().update(new_text_strings[0], justification=justification)
        self.that_text.delete('1.0', END)
        self.that_text.insert(END, new_text_strings[1])
        self.that_text.tag_configure('tag', justify=justification)
        self.that_text.tag_add('tag', 1.0, 'end')

    def clear(self):
        super().clear()
        self.that_text.delete('1.0', END)


class SSN_DropDown_Widget:
    def __init__(self, window, label_text, label_pos, dropdown_list, dropdown_pos, dropdown_block_width,
                 default_selected_item=0, justification='center'):
        self.this_label = ttk.Label(window, text=label_text)
        self.this_label.place(x=label_pos[0], y=label_pos[1])
        self.this_dropdown = ttk.Combobox(window, width=dropdown_block_width)
        self.this_dropdown['values'] = dropdown_list
        self.this_dropdown.current(default_selected_item)  # set the selected item
        self.this_dropdown.config(justify=justification)
        self.this_dropdown.place(x=dropdown_pos[0], y=dropdown_pos[1])
        pass

    def get(self):
        return self.this_dropdown.get()


class SSN_Server_UI():
    def __init__(self, window_theme="aquativo", window_title="Hello World!", window_geometry="400x400+100+100"):
        self.servertimeofday_Tick = int(round(time.time()))
        self.root_window = ThemedTk()
        self.root_window.set_theme(theme_name=window_theme)
        self.root_window.title(window_title)
        self.root_window.geometry(window_geometry)
        self.window_width = self.root_window.winfo_screenwidth()
        self.window_height = self.root_window.winfo_screenheight()
        # essential communicators
        self.mqtt_comm = None
        # self.udp_comm = None
        self.serial_comm = None
        self.COMM = False
        self.csv_data_recording = None
        ############# if we have more than one node
        self.NodeCountInGUI = 0
        self.message_type_text = list()
        self.node_select_radio_button = SSN_Radio_Button_Common_Option_Widget(self.root_window)
        self.nodeid_text = list()
        self.temperature_text = list()
        self.humidity_text = list()
        self.nodeuptime_text = list()
        self.abnormalactivity_text = list()
        ######## Machine Incoming data to be displayed
        self.machine_loadcurrents, self.machine_percentageloads, self.machine_status = [[] for _ in range(4)], [[] for _ in range(4)], [[] for _ in range(4)]
        self.machine_timeinstate, self.machine_sincewheninstate = [[] for _ in range(4)], [[] for _ in range(4)]
        self.no_connection = 0

    def start(self):
        self.root_window.mainloop()
        # threading.Thread.__init__(self)
        # self.start()

    def setup_input_interface(self, current_sensor_ratings, mac_addresses_filename, default_configs):
        # enter the SSN new MAC
        full_mac_list = get_MAC_addresses_from_file(mac_addresses_filename)
        self.ssn_mac_dropdown = SSN_DropDown_Widget(window=self.root_window, label_text="SSN MAC",
                                                    label_pos=(0, vertical_spacing * 0 + 2),
                                                    dropdown_list=full_mac_list,
                                                    dropdown_pos=(horizontal_spacing - 10, vertical_spacing * 0 + 2),
                                                    dropdown_block_width=17)
        ######## Machine Config Inputs
        self.machine_ratings, self.machine_maxloads, self.machine_thresholds = list(), list(), list()
        for i in range(4):
            # generate machine label
            rating_label_text = "M{} Sensor Rating (A)".format(i + 1)
            maxload_label_text = "M{} Max Load (A)".format(i + 1)
            thres_label_text = "M{} Threshold (A)".format(i + 1)
            # enter machine sensor rating
            rating_dropdown = SSN_DropDown_Widget(window=self.root_window, label_text=rating_label_text,
                                                  label_pos=(horizontal_spacing * 2 * i, vertical_spacing * 1 + 5),
                                                  dropdown_list=current_sensor_ratings, dropdown_pos=(
                horizontal_spacing * (2 * i + 1), vertical_spacing * 1 + 5),
                                                  dropdown_block_width=12,
                                                  default_selected_item=default_configs[0 + 3 * i])
            # enter machine max load
            maxload_text_entry = SSN_Text_Entry_Widget(window=self.root_window, label_text=maxload_label_text,
                                                       label_pos=(horizontal_spacing * 2 * i, vertical_spacing * 2 + 5),
                                                       text_entry_width=15, text_pos=(
                horizontal_spacing * (2 * i + 1), vertical_spacing * 2 + 5), default_value=default_configs[1 + 3 * i])
            # enter machine threshold current
            thresh_text_entry = SSN_Text_Entry_Widget(window=self.root_window, label_text=thres_label_text,
                                                      label_pos=(horizontal_spacing * 2 * i, vertical_spacing * 3 + 5),
                                                      text_entry_width=15, text_pos=(
                horizontal_spacing * (2 * i + 1), vertical_spacing * 3 + 5), default_value=default_configs[2 + 3 * i])
            self.machine_ratings.append(rating_dropdown)
            self.machine_maxloads.append(maxload_text_entry)
            self.machine_thresholds.append(thresh_text_entry)
            pass
        # reporting interval text input
        self.reportinterval_text_entry = SSN_Text_Entry_Widget(window=self.root_window,
                                                               label_text="Report Interval (sec)",
                                                               label_pos=(
                                                               horizontal_spacing * 2, vertical_spacing * 4 + 5),
                                                               text_entry_width=15,
                                                               text_pos=(
                                                               horizontal_spacing * (2 + 1), vertical_spacing * 4 + 5),
                                                               default_value=default_configs[12])
        pass

    def clear_status_panel(self):
        # clear node status
        for this_node in range(self.NodeCountInGUI):
            self.message_type_text[this_node].clear()
            self.nodeid_text[this_node].clear()
            # clear existing texts for node specific information
            self.temperature_text[this_node].clear()
            self.humidity_text[this_node].clear()
            self.nodeuptime_text[this_node].clear()
            self.abnormalactivity_text[this_node].clear()
            # clear existing texts for machine specific information
            for i in range(4):
                self.machine_loadcurrents[this_node][i].clear()
                self.machine_percentageloads[this_node][i].clear()
                self.machine_status[this_node][i].clear()
                self.machine_timeinstate[this_node][i].clear()
                self.machine_sincewheninstate[this_node][i].clear()
                pass
            pass
        pass

    def send_mac_btn_clicked(self):
        if self.COMM:
            # clear node status panel
            self.clear_status_panel()
            # construct and send set_mac message
            try:
                self.mqtt_comm.send_set_mac_message(mac_address=self.ssn_mac_dropdown.get())
                print('\033[34m' + "Sent MAC to SSN-{}".format(self.node_select_radio_button.getSelectedNode()))
            except IndexError:
                print(
                    '\033[31m' + "SSN Network Node Count: {}. Can't Send to SSN Indexed: {}")#.format(self.mqtt_comm.getNodeCountinNetwork(),
                 #self.node_select_radio_button.getSelectedNode() - 1))
        pass

    def send_config_btn_clicked(self):
        if self.COMM:
            # clear node status panel
            self.clear_status_panel()
            # get the configs from the GUI
            self.configs = list()
            for i in range(4):
                this_sensor_rating = self.machine_ratings[i].get()
                this_sensor_rating = int(this_sensor_rating) if this_sensor_rating != 'NONE' else 0
                self.configs.append(this_sensor_rating)
                self.configs.append(int(10 * float(self.machine_thresholds[i].get())))
                self.configs.append(int(self.machine_maxloads[i].get()))
                pass
            self.configs.append(int(self.reportinterval_text_entry.get()))
            try:
                self.mqtt_comm.send_set_config_message(config=self.configs)
                print('\033[34m' + "Sent CONFIG to SSN-{}".format(self.node_select_radio_button.getSelectedNode()))
            except IndexError:
                print(
                    '\033[31m' + "SSN Network Node Count: {}. Can't Send to SSN Indexed: {}")#.format(self.mqtt_comm.getNodeCountinNetwork(),
                  # self.node_select_radio_button.getSelectedNode() - 1))
            # change button color
            # self.config_button.config(bg='white')
        pass

    def send_timeofday_btn_clicked(self):
        if self.COMM:
            try:
                # self.udp_comm.send_set_timeofday_message(node_index=self.node_select_radio_button.getSelectedNode() - 1, current_time=self.server_time_now)
                self.mqtt_comm.send_set_timeofday_Tick_message(current_tick=utils.get_bytes_from_int(self.servertimeofday_Tick))#node_index=self.node_select_radio_button.getSelectedNode() - 1,
                print('\033[34m' + "Sent Time of Day to SSN-{}")#.format(self.node_select_radio_button.getSelectedNode()))
            except IndexError:
                print(
                    '\033[31m' + "SSN Network Node Count: {}. Can't Send to SSN Indexed: {}")#.format(self.mqtt_comm.getNodeCountinNetwork(),
                       #self.node_select_radio_button.getSelectedNode() - 1))
        pass

    def debug_reset_eeprom_btn_clicked(self):
        if self.COMM:
            # send message and clear the status texts
            try:
                self.mqtt_comm.send_debug_reset_eeprom_message()
                print(
                    '\033[34m' + "Sent CLEAR EEPROM to SSN-{}")#.format(self.node_select_radio_button.getSelectedNode()))
            except IndexError:
                print(
                    '\033[31m' + "SSN Network Node Count: {}. Can't Send to SSN Indexed: {}")#.format(self.mqtt_comm.getNodeCountinNetwork(),
                      # self.node_select_radio_button.getSelectedNode() - 1))
            # clear node status panel
            self.clear_status_panel()
        pass

    def debug_reset_ssn_btn_clicked(self):
        if self.COMM:
            # send message and clear statuss
            try:
                self.mqtt_comm.send_debug_reset_ssn_message()
                print('\033[34m' + "Sent RESET to SSN-{}".format(self.node_select_radio_button.getSelectedNode()))
            except IndexError:
                print(
                    '\033[31m' + "SSN Network Node Count: {}. Can't Send to SSN Indexed: {}")#.format(self.mqtt_comm.getNodeCountinNetwork(),
                   #    self.node_select_radio_button.getSelectedNode() - 1))
            # clear node status panel
            self.clear_status_panel()
        pass

    def setup_buttons(self):
        # update mac button
        self.mac_button = SSN_Button_Widget(window=self.root_window, button_text="Send MAC Address",
                                            button_command=self.send_mac_btn_clicked,
                                            button_pos=(2 * horizontal_spacing, vertical_spacing * 0 + 0))
        # send sensor configuration button
        self.config_button = SSN_Button_Widget(window=self.root_window, button_text="Send Configuration",
                                               button_command=self.send_config_btn_clicked,
                                               button_pos=(horizontal_spacing * 4, vertical_spacing * 4 + 5))
        # send time of day button; we will also give a display of current time of day with this
        self.servertimeofday_text = SSN_Text_Display_Widget(window=self.root_window, label_text="Server Time of Day",
                                                            label_pos=(
                                                            3 * horizontal_spacing + 52, vertical_spacing * 7),
                                                            text_size=(150, vertical_spacing), text_pos=(
            3 * horizontal_spacing + 30, vertical_spacing * 8))
        self.servertimeofday_button = SSN_Button_Widget(window=self.root_window, button_text="Send Time of Day",
                                                        button_command=self.send_timeofday_btn_clicked,
                                                        button_pos=(
                                                        3 * horizontal_spacing + 54, vertical_spacing * 9 + 5))
        self.debug_reset_eeprom_button = SSN_Button_Widget(window=self.root_window, button_text="(DEBUG) CLEAR EEPROM",
                                                           button_command=self.debug_reset_eeprom_btn_clicked,
                                                           button_pos=(
                                                           5 * horizontal_spacing + 50, vertical_spacing * 8 - 10))
        self.debug_reset_ssn_button = SSN_Button_Widget(window=self.root_window, button_text="(DEBUG) RESET SSN",
                                                        button_command=self.debug_reset_ssn_btn_clicked,
                                                        button_pos=(
                                                        5 * horizontal_spacing + 64, vertical_spacing * 9 + 5))
        self.clear_status_panel_button = SSN_Button_Widget(window=self.root_window, button_text="Clear Status Panel",
                                                           button_command=self.clear_status_panel,
                                                           button_pos=(
                                                           5 * horizontal_spacing + 69, vertical_spacing * 10 + 22))
        pass

    def GUI_Block(self):
        return (self.NodeCountInGUI - 1) * vertical_spacing * 14 + 40

    def setup_incoming_data_interface(self, NumOfNodes):
        for k in range(NumOfNodes):
            self.NodeCountInGUI += 1
            # received message/status to be displayed
            self.message_type_text.append(SSN_Text_Display_Widget(window=self.root_window, label_text="Incoming Message Type",
                                        label_pos=(0, self.GUI_Block() + vertical_spacing * 6),
                                        text_size=(110, vertical_spacing),
                                        text_pos=(horizontal_spacing + 20, self.GUI_Block() + vertical_spacing * 6)))
            # add a radio-button to chose this one when we have to send the message
            self.node_select_radio_button.add_radio(radio_text="SSN-{}".format(self.NodeCountInGUI),
                                                    radio_value=self.NodeCountInGUI,
                                                    radio_pos=(2 * horizontal_spacing + 20,
                                                               self.GUI_Block() + vertical_spacing * 6))
            # SSN Node ID to be displayed
            self.nodeid_text.append(SSN_Text_Display_Widget(window=self.root_window, label_text="Node ID",
                                                            label_pos=(0, self.GUI_Block() + vertical_spacing * 7),
                                                            text_size=(110, vertical_spacing), text_pos=(
                horizontal_spacing + 20, self.GUI_Block() + vertical_spacing * 7)))
            # temperature to be displayed
            self.temperature_text.append(SSN_Text_Display_Widget(window=self.root_window, label_text="Temperature ({}C)".format(chr(176)),
                                        label_pos=(0, self.GUI_Block() + vertical_spacing * 8),
                                        text_size=(110, vertical_spacing),
                                        text_pos=(horizontal_spacing + 20, self.GUI_Block() + vertical_spacing * 8)))
            # humidity to be displayed
            self.humidity_text.append(SSN_Text_Display_Widget(window=self.root_window, label_text="Relative Humidity (%)",
                                        label_pos=(0, self.GUI_Block() + vertical_spacing * 9),
                                        text_size=(110, vertical_spacing),
                                        text_pos=(horizontal_spacing + 20, self.GUI_Block() + vertical_spacing * 9)))
            # node uptime to be displayed
            self.nodeuptime_text.append(SSN_Text_Display_Widget(window=self.root_window, label_text="Node Up Time in (sec)",
                                        label_pos=(0, self.GUI_Block() + vertical_spacing * 10),
                                        text_size=(110, vertical_spacing),
                                        text_pos=(horizontal_spacing + 20, self.GUI_Block() + vertical_spacing * 10)))
            # abnormal activity to be displayed
            self.abnormalactivity_text.append(SSN_Text_Display_Widget(window=self.root_window, label_text="Abnormal Activity",
                                        label_pos=(0, self.GUI_Block() + vertical_spacing * 11),
                                        text_size=(110, vertical_spacing),
                                        text_pos=(horizontal_spacing + 20, self.GUI_Block() + vertical_spacing * 11),
                                        color='green'))

            for i in range(4):
                # generate machine labels
                loadcurrent_label_text = "M{} Load Current (A)".format(i + 1)
                percentload_label_text = "M{} Percentage Load (%)".format(i + 1)
                state_label_text = "M{} State (OFF/IDLE/ON)".format(i + 1)
                duration_label_text = "M{} Time In State (sec)".format(i + 1)
                timestamp_label_text = "M{} State Time Stamp".format(i + 1)
                # machine load current
                loadcurrent_text = SSN_Text_Display_Widget(window=self.root_window, label_text=loadcurrent_label_text,
                                                           label_pos=(horizontal_spacing * 2 * i,
                                                                      self.GUI_Block() + vertical_spacing * 12 + 20),
                                                           text_size=(80, vertical_spacing),
                                                           text_pos=((2 * i + 1) * horizontal_spacing + 20,
                                                                     self.GUI_Block() + vertical_spacing * 12 + 20))
                percentload_text_entry = SSN_Text_Display_Widget(window=self.root_window,
                                                                 label_text=percentload_label_text,
                                                                 label_pos=(horizontal_spacing * 2 * i,
                                                                            self.GUI_Block() + vertical_spacing * 13 + 20),
                                                                 text_size=(80, vertical_spacing),
                                                                 text_pos=(horizontal_spacing * (2 * i + 1) + 20,
                                                                           self.GUI_Block() + vertical_spacing * 13 + 20))
                # machine state
                state_text_entry = SSN_Text_Display_Widget(window=self.root_window, label_text=state_label_text,
                                                           label_pos=(horizontal_spacing * 2 * i,
                                                                      self.GUI_Block() + vertical_spacing * 14 + 20),
                                                           text_size=(80, vertical_spacing), text_pos=(
                    horizontal_spacing * (2 * i + 1) + 20, self.GUI_Block() + vertical_spacing * 14 + 20))
                # machine state duration
                duration_text_entry = SSN_Text_Display_Widget(window=self.root_window, label_text=duration_label_text,
                                                              label_pos=(horizontal_spacing * 2 * i,
                                                                         self.GUI_Block() + vertical_spacing * 15 + 20),
                                                              text_size=(80, vertical_spacing),
                                                              text_pos=(horizontal_spacing * (2 * i + 1) + 20,
                                                                        self.GUI_Block() + vertical_spacing * 15 + 20))
                # machine state timestamp
                timestamp_dual_text_entry = SSN_Dual_Text_Display_Widget(window=self.root_window,
                                                                         label_text=timestamp_label_text,
                                                                         label_pos=(horizontal_spacing * 2 * i,
                                                                                    self.GUI_Block() + vertical_spacing * 16 + 20),
                                                                         text_size=(80, vertical_spacing),
                                                                         text_pos1=(
                                                                         horizontal_spacing * (2 * i + 1) + 20,
                                                                         self.GUI_Block() + vertical_spacing * 16 + 20),
                                                                         text_pos2=(
                                                                         horizontal_spacing * (2 * i + 1) + 20,
                                                                         self.GUI_Block() + vertical_spacing * 17 + 20))
                self.machine_loadcurrents[self.NodeCountInGUI - 1].append(loadcurrent_text)
                self.machine_percentageloads[self.NodeCountInGUI - 1].append(percentload_text_entry)
                self.machine_status[self.NodeCountInGUI - 1].append(state_text_entry)
                self.machine_timeinstate[self.NodeCountInGUI - 1].append(duration_text_entry)
                self.machine_sincewheninstate[self.NodeCountInGUI - 1].append(timestamp_dual_text_entry)
                pass
            pass
        # set default node for sending messages
        self.node_select_radio_button.radio_buttons[0].invoke()
        pass

    def setup_serial_communication(self, serial_port='COM5', baudrate=19200,
                                   log_file='../serial_log-110920-130920.txt'):
        self.serial_comm = SERIAL_COMM(serial_port, baudrate, log_file)
        pass

    def setup_mqtt_communication(self):
        # essential UDP communicator
        self.mqtt_comm = MQTT_COMM()
        connection_status = self.mqtt_comm.mqttclientsetup()
        if connection_status is None:
            print("Cannot Connect to Network!!!")
            return
        # invoke it just once
        self.read_messages_and_update_UI()
        self.COMM = True
        pass


    def setup_csv_data_recording(self, csv_file):
        this_date = datetime.datetime.fromtimestamp(int(round(time.time())))
        file_name, extension = os.path.splitext(csv_file)
        self.csv_data_file = file_name
        self.csv_data_recording = True
        pass

    def read_messages_and_update_UI(self):
        # node_index = 1
        # check serial comm for messages
        # if self.serial_comm:
        #     self.serial_comm.log()
        self.servertimeofday_text.update(new_text_string=self.servertimeofday_Tick)
        # recall this method after another second
        self.root_window.after(200, self.read_messages_and_update_UI)
    pass

    # The callback for when a PUBLISH message is received from the server.


class MQTT_COMM:
    def __init__(self):
        # for multiple nodes
        # self.SSN_Network_Address_Mapping = {}
        self.SSN_Network_Nodes = list()
        self.Server_UI = None
        pass

    # The callback for when the client receives a CONNACK response from the server.
    def on_connect(self, client, userdata, flags, rc):
        print("Connected with result code " + str(rc))
        # Subscribing in on_connect() means that if we lose the connection and
        # reconnect then subscriptions will be renewed.
        # self.client.subscribe("/SSN/")

    def on_message(self, client, userdata, message):
        self.Server_UI = SSN_Server_UI()
        print("message received ", message.payload)
        print(message.payload)
        message_received = bytes(message.payload)
        message_id, params = self.decipher_node_message(message_received)
        # # for a in in_message:
        # #     #print(a.topic)
        # #     # print(a.payload)
        # #     # in_message=a.payload
        # #     receivedmsg=bytes(a.payload)
        # #     message_id, params = self.mqtt_comm.decipher_node_message(receivedmsg)
        # print(message_id)
        # print(params)
        # # check if a valid message was received or not
        # # for node_index in range(10):
        #     # if message_id == -1:
        #     #     self.no_connection += 1
        #     #     if self.no_connection > 10:
        #     #         self.no_connection = 0
        #     #         print('\033[30m' + "XXX Nothing Received XXX")
        #     #     pass
        #     # else:
        #     #     self.no_connection = 0
        # message type and node id will always be displayed
        self.Server_UI.message_type_text.update(new_text_string=SSN_MessageID_to_Type[message_id], justification='left')
        self.Server_UI.nodeid_text.update(new_text_string=params[0])
        # basic get messages received?
        if message_id == SSN_MessageType_to_ID['GET_MAC']:
            print('\033[34m' + "Received GET_MAC from SSN-{}")  # .format(node_index+1))
        elif message_id == SSN_MessageType_to_ID['GET_TIMEOFDAY']:
            print('\033[34m' + "Received GET_TIMEOFDAY from SSN-{}")  # format(node_index+1))
            # automate set time of day
            print('\033[34m' + "Sending SET_TIMEOFDAY to SSN-{}")  # .format(node_index+1))
            self.send_set_timeofday_Tick_message(current_tick=utils.get_bytes_from_int(self.Server_UI.servertimeofday_Tick))#node_index=self.Server_UI.node_select_radio_button.getSelectedNode() - 1
            print('\033[34m' + "Sent Time of Day to SSN-{}".format(self.node_select_radio_button.getSelectedNode()))
        elif message_id == SSN_MessageType_to_ID['GET_CONFIG']:
            print('\033[34m' + "Received GET_CONFIG from SSN-{}")  # .format(node_index+1))
        # configs have been acknowledged?
        elif message_id == SSN_MessageType_to_ID['ACK_CONFIG']:
            configs_acknowledged = params[1]  # it is a list
            if configs_acknowledged == self.configs:
                print('\033[34m' + "Received CONFIG ACK from SSN-{}")  # .format(node_index + 1))
                # self.config_button.config(bg='light green')
                pass
            pass
        # status update message brings the ssn heartbeat status
        elif message_id == SSN_MessageType_to_ID['STATUS_UPDATE']:
            print('\033[34m' + "Received Status Update from SSN-{}")#.format(node_index+1))
            self.temperature_text.update(new_text_string=params[1])
            self.humidity_text.update(new_text_string=params[2])
            self.nodeuptime_text.update(new_text_string=self.Server_UI.servertimeofday_Tick - params[3])  # get the difference of static tick and current tick
            activity_level = SSN_ActivityLevelID_to_Type[params[4]]
            # get activity level of the SSN and display properly
            self.Server_UI.abnormalactivity_text.update(new_text_string=activity_level)
            if activity_level == 'NORMAL':
                self.Server_UI.abnormalactivity_text.change_text_color(new_color='green')
            else:
                self.Server_UI.abnormalactivity_text.change_text_color(new_color='red')
            machine_state_timestamps = []
            for i in range(4):
                self.Server_UI.machine_loadcurrents[i].update(new_text_string=params[5 + i])
                self.Server_UI.machine_percentageloads[i].update(new_text_string=params[9 + i])
                self.Server_UI.machine_status[i].update(new_text_string=Machine_State_ID_to_State[params[13 + i]])
                state_timestamp_tick = params[17 + i]
                if state_timestamp_tick != 0:
                    # elapsed_time_in_state = self.servertimeofday_Tick - state_timestamp_tick
                    good_time = datetime.datetime.fromtimestamp(state_timestamp_tick)
                    exact_time_strings = ["{}:{}:{}".format(good_time.hour, good_time.minute, good_time.second),
                                          "{}/{}/{}".format(good_time.day, good_time.month, good_time.year)]
                else:
                    # elapsed_time_in_state = state_timestamp_tick
                    exact_time_strings = ["0:0:0", "0/0/0"]
                machine_state_timestamps.append(exact_time_strings)
                self.Server_UI.machine_timeinstate[i].update(new_text_string=params[21 + i])
                self.Server_UI.machine_sincewheninstate[i].update(new_text_strings=machine_state_timestamps[i])
                pass
                # append this data to our CSV file
                # if self.csv_data_recording:
                #     # insertiontimestamp, node_id, node_uptime, activitylevel,
                #     # temperature, humidity,
                #     # M1_load, M1_load%, M1_state, M1_statetimestamp, M1_stateduration,
                #     # M2_*...
                #     server_time_of_the_day = datetime.datetime.fromtimestamp(self.servertimeofday_Tick)
                #     data_packet = [server_time_of_the_day, params[0], datetime.datetime.fromtimestamp(params[3]), activity_level,
                #                    params[1], params[2],
                #                    params[5], params[9], params[13], datetime.datetime.fromtimestamp(params[17]), params[21],
                #                    params[6], params[10], params[14], datetime.datetime.fromtimestamp(params[18]), params[22]]
                #     with open(self.csv_data_file+"-{}-{}-{}".format(server_time_of_the_day.day, server_time_of_the_day.month, server_time_of_the_day.year)+".csv",
                #               'a', newline="") as f:
                #         writer = csv.writer(f)
                #         writer.writerow(data_packet)
                #         pass
            pass
        pass

    def mqttclientsetup(self):
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.connect(broker_ip, 1883, 60)
        self.client.subscribe("/SSN/")
        self.client.loop_start()  # start the loop
        return True

    def decipher_node_message(self, node_message=None):
        print("HERE")
        print(node_message[0])
        print(node_message[1])
        print(node_message[2])
        # check message
        # for i in range(len(node_message)):
        #     print("{}, ".format(node_message[i]), end='')
        # message id and node id are always present in each message
        node_message_id = node_message[2]
        node_id = utils.get_MAC_id_from_bytes(high_byte=node_message[0], low_byte=node_message[1])
        # basic get messages received?
        # GET MAC message is received?
        if node_message_id == SSN_MessageType_to_ID['GET_MAC']:
            print("EXIT")
            # print(node_message_id)
            # print([node_id])
            return node_message_id, [node_id]

        # Get configurations message is received?
        elif node_message_id == SSN_MessageType_to_ID['GET_CONFIG']:
            return node_message_id, [node_id]

        # acknowledge configurations message is received from the SSN?
        elif node_message_id == SSN_MessageType_to_ID['ACK_CONFIG']:
            configs_received = list()
            for i in range(4):
                configs_received.append(node_message[3 + 3 * i])
                configs_received.append(node_message[4 + 3 * i])
                configs_received.append(node_message[5 + 3 * i])
                pass
            configs_received.append(node_message[15])
            return node_message_id, [node_id, configs_received]

        # Get time of day is received from the node?
        elif node_message_id == SSN_MessageType_to_ID['GET_TIMEOFDAY']:
            return node_message_id, [node_id]

        # Status update is received?
        elif node_message_id == SSN_MessageType_to_ID['STATUS_UPDATE']:
            # get node specific information
            temperature = utils.get_word_from_bytes(high_byte=node_message[3], low_byte=node_message[4]) / 10.0
            humidity = utils.get_word_from_bytes(high_byte=node_message[5], low_byte=node_message[6]) / 10.0
            state_flags = node_message[7]
            ssn_uptime = utils.get_int_from_bytes(highest_byte=node_message[56], higher_byte=node_message[57],
                                                  high_byte=node_message[58], low_byte=node_message[59])
            abnormal_activity = node_message[60]
            # get machine specific information
            machine_load_currents, machine_load_percentages, machine_status, machine_state_timestamp, machine_state_duration = list(), list(), list(), list(), list()
            # print(node_message)
            for i in range(4):
                machine_load_currents.append(utils.get_word_from_bytes(high_byte=node_message[8 + i * offset],
                                                                       low_byte=node_message[9 + i * offset]) / 100.0)
                machine_load_percentages.append(node_message[10 + i * offset])
                machine_status.append(node_message[11 + i * offset])
                machine_state_timestamp.append(utils.get_int_from_bytes(highest_byte=node_message[12 + i * offset],
                                                                        higher_byte=node_message[13 + i * offset],
                                                                        high_byte=node_message[14 + i * offset],
                                                                        low_byte=node_message[15 + i * offset]))
                machine_state_duration.append(utils.get_int_from_bytes(highest_byte=node_message[16 + i * offset],
                                                                       higher_byte=node_message[17 + i * offset],
                                                                       high_byte=node_message[18 + i * offset],
                                                                       low_byte=node_message[19 + i * offset]))
                pass
            return node_message_id, [node_id, temperature, humidity, ssn_uptime, abnormal_activity,
                                     *machine_load_currents, *machine_load_percentages, *machine_status,
                                     *machine_state_timestamp, *machine_state_duration]
        return

    def construct_set_mac_message(self, mac_address):
        mac_address_in_bytes = get_mac_bytes_from_mac_string(mac_address=mac_address)
        set_mac_message = [SSN_MessageType_to_ID['SET_MAC'], *mac_address_in_bytes]
        return bytearray(set_mac_message)

    def send_set_mac_message(self, mac_address):
        set_mac_message = self.construct_set_mac_message(mac_address=mac_address)
        self.client.publish("/SSN/CONFIG", set_mac_message)
        print("Published-Sent Set MAC Message!")
        # self.client_socket.sendto(set_mac_message, self.SSN_Network_Address_Mapping[self.SSN_Network_Nodes[node_index]])
        pass

    def construct_set_timeofday_message(self, current_time):
        set_timeofday_message = [SSN_MessageType_to_ID['SET_TIMEOFDAY'], int(current_time.hour),
                                 int(current_time.minute), int(current_time.second),
                                 int(current_time.day), int(current_time.month), int(current_time.year - 2000)]
        return bytearray(set_timeofday_message)

    def send_set_timeofday_message(self, current_time):
        set_timeofday_message = self.construct_set_timeofday_message(current_time=current_time)
        self.client.publish("/SSN/CONFIG", set_timeofday_message)
        print("Published-Sent_set_timeofday_message!")
        # self.client_socket.sendto(set_timeofday_message, self.SSN_Network_Address_Mapping[self.SSN_Network_Nodes[node_index]])
        pass

    def construct_set_timeofday_Tick_message(self, current_Tick):
        set_timeofday_Tick_message = [SSN_MessageType_to_ID['SET_TIMEOFDAY'], current_Tick[0], current_Tick[1],
                                      current_Tick[2], current_Tick[3]]
        return bytearray(set_timeofday_Tick_message)

    def send_set_timeofday_Tick_message(self, current_tick):
        set_timeofday_message = self.construct_set_timeofday_Tick_message(current_Tick=current_tick)
        self.client.publish("/SSN/CONFIG", set_timeofday_message)
        print("Published-Sent_set_timeofday_tick message!")
        # self.client_socket.sendto(set_timeofday_message, self.SSN_Network_Address_Mapping[self.SSN_Network_Nodes[node_index]])
        pass

    def construct_set_config_message(self, config):
        set_config_message = [SSN_MessageType_to_ID['SET_CONFIG'], *config]
        return bytearray(set_config_message)

    def send_set_config_message(self, config):
        set_config_message = self.construct_set_config_message(config=config)
        self.client.publish("/SSN/CONFIG", set_config_message)
        print("Published-Sent_set_timeofday_tick message!")
        # self.client_socket.sendto(set_config_message, self.SSN_Network_Address_Mapping[self.SSN_Network_Nodes[node_index]])
        pass

    def construct_debug_reset_eeprom_message(self):
        debug_reset_eeprom_message = [SSN_MessageType_to_ID['DEBUG_EEPROM_CLEAR']]
        return bytearray(debug_reset_eeprom_message)

    def send_debug_reset_eeprom_message(self):
        debug_reset_eeprom_message = self.construct_debug_reset_eeprom_message()
        self.client.publish("/SSN/CONFIG", debug_reset_eeprom_message)
        print("Published-debug_reset_eeprom_message message!")
        # self.client_socket.sendto(debug_reset_eeprom_message, self.SSN_Network_Address_Mapping[self.SSN_Network_Nodes[node_index]])
        pass

    def construct_debug_reset_ssn_message(self):
        debug_reset_ssn_message = [SSN_MessageType_to_ID['DEBUG_RESET_SSN']]
        return bytearray(debug_reset_ssn_message)

    def send_debug_reset_ssn_message(self):
        debug_reset_ssn_message = self.construct_debug_reset_ssn_message()
        self.client.publish("/SSN/CONFIG", debug_reset_ssn_message)
        print("Published-debug_reset_ssn_message message!")
        # self.client_socket.sendto(debug_reset_ssn_message, self.SSN_Network_Address_Mapping[self.SSN_Network_Nodes[node_index]])
        pass

    def getNodeCountinNetwork(self):
        return len(self.SSN_Network_Address_Mapping)
