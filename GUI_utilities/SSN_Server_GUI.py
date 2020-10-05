import csv
import time
import datetime
from tkinter import *  # Normal Tkinter.* widgets are not themed!
from ttkthemes import ThemedTk, ThemedStyle
from tkinter import ttk
from UDP_COMM.udp_communication import *
from SERIAL_COMM.serial_communication import *
from MAC_utilities.MAC_utils import get_MAC_addresses_from_file

vertical_spacing = 21
horizontal_spacing = 120
Machine_State_ID_to_State = {0: 'OFF', 1: 'IDLE', 2: 'ON'}


class SSN_Button_Widget:
    def __init__(self, window, button_text, button_command, button_pos):
        self.this_button = ttk.Button(window, text=button_text, command=button_command) #bg="white", fg="blue"
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
    def __init__(self, window, label_text, label_pos, text_entry_width, text_pos, default_value='100', justification='center'):
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
    def __init__(self, window, label_text, label_pos, text_size, text_pos1, text_pos2, color='black', justification='center'):
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
    def __init__(self, window, label_text, label_pos, dropdown_list, dropdown_pos, dropdown_block_width, default_selected_item=0, justification='center'):
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
        self.root_window = ThemedTk()
        self.root_window.set_theme(theme_name=window_theme)
        self.root_window.title(window_title)
        self.root_window.geometry(window_geometry)
        self.window_width = self.root_window.winfo_screenwidth()
        self.window_height = self.root_window.winfo_screenheight()
        # essential communicators
        self.udp_comm = None
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
        pass

    def start(self):
        self.root_window.mainloop()
        # threading.Thread.__init__(self)
        # self.start()

    def setup_input_interface(self, current_sensor_ratings, mac_addresses_filename, default_configs):
        # enter the SSN new MAC
        full_mac_list = get_MAC_addresses_from_file(mac_addresses_filename)
        self.ssn_mac_dropdown = SSN_DropDown_Widget(window=self.root_window, label_text="SSN MAC", label_pos=(0, vertical_spacing*0 + 2),
                                                                        dropdown_list=full_mac_list, dropdown_pos=(horizontal_spacing-10, vertical_spacing*0 + 2),
                                                                        dropdown_block_width=17)
        ######## Machine Config Inputs
        self.machine_ratings, self.machine_maxloads, self.machine_thresholds = list(), list(), list()
        for i in range(4):
            # generate machine label
            rating_label_text = "M{} Sensor Rating (A)".format(i+1)
            maxload_label_text = "M{} Max Load (A)".format(i+1)
            thres_label_text = "M{} Threshold (A)".format(i+1)
            # enter machine sensor rating
            rating_dropdown = SSN_DropDown_Widget(window=self.root_window, label_text=rating_label_text, label_pos=(horizontal_spacing*2*i, vertical_spacing * 1 + 5),
                                                  dropdown_list=current_sensor_ratings, dropdown_pos=(horizontal_spacing*(2*i+1), vertical_spacing * 1 + 5),
                                                  dropdown_block_width=12, default_selected_item=default_configs[0+3*i])
            # enter machine max load
            maxload_text_entry = SSN_Text_Entry_Widget(window=self.root_window, label_text=maxload_label_text, label_pos=(horizontal_spacing*2*i, vertical_spacing * 2 + 5),
                                                       text_entry_width=15, text_pos=(horizontal_spacing*(2*i+1), vertical_spacing * 2 + 5), default_value=default_configs[1+3*i])
            # enter machine threshold current
            thresh_text_entry = SSN_Text_Entry_Widget(window=self.root_window, label_text=thres_label_text, label_pos=(horizontal_spacing*2*i, vertical_spacing * 3 + 5),
                                                      text_entry_width=15, text_pos=(horizontal_spacing*(2*i+1), vertical_spacing * 3 + 5), default_value=default_configs[2+3*i])
            self.machine_ratings.append(rating_dropdown)
            self.machine_maxloads.append(maxload_text_entry)
            self.machine_thresholds.append(thresh_text_entry)
            pass
        # reporting interval text input
        self.reportinterval_text_entry = SSN_Text_Entry_Widget(window=self.root_window, label_text="Report Interval (sec)",
                                                               label_pos=(horizontal_spacing*2, vertical_spacing * 4 + 5), text_entry_width=15,
                                                               text_pos=(horizontal_spacing*(2+1), vertical_spacing * 4 + 5), default_value=default_configs[12])
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
                self.udp_comm.send_set_mac_message(node_index=self.node_select_radio_button.getSelectedNode() - 1, mac_address=self.ssn_mac_dropdown.get())
                print('\033[34m' + "Sent MAC to SSN-{}".format(self.node_select_radio_button.getSelectedNode()))
            except IndexError:
                print('\033[31m' + "SSN Network Node Count: {}. Can't Send to SSN Indexed: {}".format(self.udp_comm.getNodeCountinNetwork(),
                                                                                                      self.node_select_radio_button.getSelectedNode() - 1))
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
                self.configs.append(int(10*float(self.machine_thresholds[i].get())))
                self.configs.append(int(self.machine_maxloads[i].get()))
                pass
            self.configs.append(int(self.reportinterval_text_entry.get()))
            try:
                self.udp_comm.send_set_config_message(node_index=self.node_select_radio_button.getSelectedNode()-1, config=self.configs)
                print('\033[34m' + "Sent CONFIG to SSN-{}".format(self.node_select_radio_button.getSelectedNode()))
            except IndexError:
                print('\033[31m' + "SSN Network Node Count: {}. Can't Send to SSN Indexed: {}".format(self.udp_comm.getNodeCountinNetwork(),
                                                                                                      self.node_select_radio_button.getSelectedNode() - 1))
            # change button color
            # self.config_button.config(bg='white')
        pass

    def send_timeofday_btn_clicked(self):
        if self.COMM:
            try:
                # self.udp_comm.send_set_timeofday_message(node_index=self.node_select_radio_button.getSelectedNode() - 1, current_time=self.server_time_now)
                self.udp_comm.send_set_timeofday_Tick_message(node_index=self.node_select_radio_button.getSelectedNode() - 1,
                                                              current_tick=utils.get_bytes_from_int(self.servertimeofday_Tick))
                print('\033[34m' + "Sent Time of Day to SSN-{}".format(self.node_select_radio_button.getSelectedNode()))
            except IndexError:
                print('\033[31m' + "SSN Network Node Count: {}. Can't Send to SSN Indexed: {}".format(self.udp_comm.getNodeCountinNetwork(),
                                                                                                      self.node_select_radio_button.getSelectedNode() - 1))
        pass

    def debug_reset_eeprom_btn_clicked(self):
        if self.COMM:
            # send message and clear the status texts
            try:
                self.udp_comm.send_debug_reset_eeprom_message(node_index=self.node_select_radio_button.getSelectedNode() - 1)
                print('\033[34m' + "Sent CLEAR EEPROM to SSN-{}".format(self.node_select_radio_button.getSelectedNode()))
            except IndexError:
                print('\033[31m' + "SSN Network Node Count: {}. Can't Send to SSN Indexed: {}".format(self.udp_comm.getNodeCountinNetwork(),
                                                                                                      self.node_select_radio_button.getSelectedNode() - 1))
            # clear node status panel
            self.clear_status_panel()
        pass

    def debug_reset_ssn_btn_clicked(self):
        if self.COMM:
            # send message and clear statuss
            try:
                self.udp_comm.send_debug_reset_ssn_message(node_index=self.node_select_radio_button.getSelectedNode() - 1)
                print('\033[34m' + "Sent RESET to SSN-{}".format(self.node_select_radio_button.getSelectedNode()))
            except IndexError:
                print('\033[31m' + "SSN Network Node Count: {}. Can't Send to SSN Indexed: {}".format(self.udp_comm.getNodeCountinNetwork(),
                                                                                                      self.node_select_radio_button.getSelectedNode() - 1))
            # clear node status panel
            self.clear_status_panel()
        pass

    def setup_buttons(self):
        # update mac button
        self.mac_button = SSN_Button_Widget(window=self.root_window, button_text="Send MAC Address", button_command=self.send_mac_btn_clicked,
                                            button_pos=(2*horizontal_spacing, vertical_spacing*0+0))
        # send sensor configuration button
        self.config_button = SSN_Button_Widget(window=self.root_window, button_text="Send Configuration", button_command=self.send_config_btn_clicked,
                                               button_pos=(horizontal_spacing*4, vertical_spacing * 4 + 5))
        # send time of day button; we will also give a display of current time of day with this
        self.servertimeofday_text = SSN_Text_Display_Widget(window=self.root_window, label_text="Server Time of Day", label_pos=(3*horizontal_spacing+52, vertical_spacing * 7),
                                                            text_size=(150, vertical_spacing), text_pos=(3*horizontal_spacing+30, vertical_spacing * 8))
        self.servertimeofday_button = SSN_Button_Widget(window=self.root_window, button_text="Send Time of Day", button_command=self.send_timeofday_btn_clicked,
                                                        button_pos=(3*horizontal_spacing+54, vertical_spacing * 9 + 5))
        self.debug_reset_eeprom_button = SSN_Button_Widget(window=self.root_window, button_text="(DEBUG) CLEAR EEPROM", button_command=self.debug_reset_eeprom_btn_clicked,
                                                           button_pos=(5*horizontal_spacing+50, vertical_spacing * 8-10))
        self.debug_reset_ssn_button = SSN_Button_Widget(window=self.root_window, button_text="(DEBUG) RESET SSN", button_command=self.debug_reset_ssn_btn_clicked,
                                                        button_pos=(5 * horizontal_spacing + 64, vertical_spacing * 9 + 5))
        self.clear_status_panel_button = SSN_Button_Widget(window=self.root_window, button_text="Clear Status Panel", button_command=self.clear_status_panel,
                                                        button_pos=(5 * horizontal_spacing + 69, vertical_spacing * 10 + 22))
        pass

    def GUI_Block(self):
        return (self.NodeCountInGUI - 1) * vertical_spacing * 14 + 40

    def setup_incoming_data_interface(self, NumOfNodes):
        for k in range(NumOfNodes):
            self.NodeCountInGUI += 1
            # received message/status to be displayed
            self.message_type_text.append(SSN_Text_Display_Widget(window=self.root_window, label_text="Incoming Message Type", label_pos=(0, self.GUI_Block() + vertical_spacing*6),
                                                                  text_size=(110, vertical_spacing), text_pos=(horizontal_spacing+20, self.GUI_Block() + vertical_spacing*6)))
            # add a radio-button to chose this one when we have to send the message
            self.node_select_radio_button.add_radio(radio_text="SSN-{}".format(self.NodeCountInGUI), radio_value=self.NodeCountInGUI,
                                                    radio_pos=(2*horizontal_spacing+20, self.GUI_Block() + vertical_spacing*6))
            # SSN Node ID to be displayed
            self.nodeid_text.append(SSN_Text_Display_Widget(window=self.root_window, label_text="Node ID", label_pos=(0, self.GUI_Block() + vertical_spacing * 7),
                                                            text_size=(110, vertical_spacing), text_pos=(horizontal_spacing + 20, self.GUI_Block() + vertical_spacing * 7)))
            # temperature to be displayed
            self.temperature_text.append(SSN_Text_Display_Widget(window=self.root_window, label_text="Temperature ({}C)".format(chr(176)),
                                                                 label_pos=(0, self.GUI_Block() + vertical_spacing*8), text_size=(110, vertical_spacing),
                                                                 text_pos=(horizontal_spacing+20, self.GUI_Block() + vertical_spacing*8)))
            # humidity to be displayed
            self.humidity_text.append(SSN_Text_Display_Widget(window=self.root_window, label_text="Relative Humidity (%)", label_pos=(0, self.GUI_Block() + vertical_spacing*9),
                                                              text_size=(110, vertical_spacing), text_pos=(horizontal_spacing+20, self.GUI_Block() + vertical_spacing*9)))
            # node uptime to be displayed
            self.nodeuptime_text.append(SSN_Text_Display_Widget(window=self.root_window, label_text="Node Up Time in (sec)", label_pos=(0, self.GUI_Block() + vertical_spacing * 10),
                                                                text_size=(110, vertical_spacing), text_pos=(horizontal_spacing + 20, self.GUI_Block() + vertical_spacing * 10)))
            # abnormal activity to be displayed
            self.abnormalactivity_text.append(SSN_Text_Display_Widget(window=self.root_window, label_text="Abnormal Activity", label_pos=(0, self.GUI_Block() + vertical_spacing * 11),
                                                                      text_size=(110, vertical_spacing), text_pos=(horizontal_spacing + 20, self.GUI_Block() + vertical_spacing * 11),
                                                                      color='green'))

            for i in range(4):
                # generate machine labels
                loadcurrent_label_text = "M{} Load Current (A)".format(i+1)
                percentload_label_text = "M{} Percentage Load (%)".format(i+1)
                state_label_text = "M{} State (OFF/IDLE/ON)".format(i+1)
                duration_label_text = "M{} Time In State (sec)".format(i+1)
                timestamp_label_text = "M{} State Time Stamp".format(i+1)
                # machine load current
                loadcurrent_text = SSN_Text_Display_Widget(window=self.root_window, label_text=loadcurrent_label_text,
                                                           label_pos=(horizontal_spacing * 2 * i, self.GUI_Block() + vertical_spacing * 12 + 20), text_size=(80, vertical_spacing),
                                                           text_pos=((2*i+1)*horizontal_spacing + 20, self.GUI_Block() + vertical_spacing * 12 + 20))
                percentload_text_entry = SSN_Text_Display_Widget(window=self.root_window, label_text=percentload_label_text,
                                                                 label_pos=(horizontal_spacing * 2 * i, self.GUI_Block() + vertical_spacing * 13 + 20), text_size=(80, vertical_spacing),
                                                                 text_pos=(horizontal_spacing * (2 * i + 1) + 20, self.GUI_Block() + vertical_spacing * 13 + 20))
                # machine state
                state_text_entry = SSN_Text_Display_Widget(window=self.root_window, label_text=state_label_text,
                                                           label_pos=(horizontal_spacing * 2 * i, self.GUI_Block() + vertical_spacing * 14 + 20),
                                                           text_size=(80, vertical_spacing), text_pos=(horizontal_spacing * (2*i+1) + 20, self.GUI_Block() + vertical_spacing*14 + 20))
                # machine state duration
                duration_text_entry = SSN_Text_Display_Widget(window=self.root_window, label_text=duration_label_text,
                                                              label_pos=(horizontal_spacing * 2 * i, self.GUI_Block() + vertical_spacing * 15 + 20), text_size=(80, vertical_spacing),
                                                              text_pos=(horizontal_spacing * (2 * i + 1) + 20, self.GUI_Block() + vertical_spacing * 15 + 20))
                # machine state timestamp
                timestamp_dual_text_entry = SSN_Dual_Text_Display_Widget(window=self.root_window, label_text=timestamp_label_text,
                                                                         label_pos=(horizontal_spacing * 2 * i, self.GUI_Block() + vertical_spacing * 16 + 20),
                                                                         text_size=(80, vertical_spacing),
                                                                         text_pos1=(horizontal_spacing * (2 * i + 1) + 20, self.GUI_Block() + vertical_spacing * 16 + 20),
                                                                         text_pos2=(horizontal_spacing * (2 * i + 1) + 20, self.GUI_Block() + vertical_spacing * 17 + 20))
                self.machine_loadcurrents[self.NodeCountInGUI-1].append(loadcurrent_text)
                self.machine_percentageloads[self.NodeCountInGUI-1].append(percentload_text_entry)
                self.machine_status[self.NodeCountInGUI-1].append(state_text_entry)
                self.machine_timeinstate[self.NodeCountInGUI-1].append(duration_text_entry)
                self.machine_sincewheninstate[self.NodeCountInGUI-1].append(timestamp_dual_text_entry)
                pass
            pass
        # set default node for sending messages
        self.node_select_radio_button.radio_buttons[0].invoke()
        pass

    def setup_serial_communication(self, serial_port='COM5', baudrate=19200, log_file='../serial_log-110920-130920.txt'):
        self.serial_comm = SERIAL_COMM(serial_port, baudrate, log_file)
        pass

    def setup_udp_communication(self, server_end):
        # essential UDP communicator
        self.udp_comm = UDP_COMM()
        connection_status = self.udp_comm.udp_setup_connection(server_address=server_end[0], server_port=server_end[1])
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
        # check serial comm for messages
        if self.serial_comm:
            self.serial_comm.log()
        self.servertimeofday_Tick = int(round(time.time()))
        self.servertimeofday_text.update(new_text_string=self.servertimeofday_Tick)
        # receive the incoming message
        node_index, message_id, params = self.udp_comm.read_udp_message()
        # check if a valid message was received or not
        if node_index == -1 and message_id == -1:
            self.no_connection += 1
            if self.no_connection > 10:
                self.no_connection = 0
                print('\033[30m' + "XXX Nothing Received XXX")
            pass
        else:
            self.no_connection = 0
            # message type and node id will always be displayed
            self.message_type_text[node_index].update(new_text_string=SSN_MessageID_to_Type[message_id], justification='left')
            self.nodeid_text[node_index].update(new_text_string=params[0])
            # basic get messages received?
            if message_id == SSN_MessageType_to_ID['GET_MAC']:
                print('\033[34m' + "Received GET_MAC from SSN-{}".format(node_index+1))
            elif message_id == SSN_MessageType_to_ID['GET_TIMEOFDAY']:
                print('\033[34m' + "Received GET_TIMEOFDAY from SSN-{}".format(node_index+1))
                # automate set time of day
                print('\033[34m' + "Sending SET_TIMEOFDAY to SSN-{}".format(node_index+1))
                self.udp_comm.send_set_timeofday_Tick_message(node_index=self.node_select_radio_button.getSelectedNode() - 1,
                                                              current_tick=utils.get_bytes_from_int(self.servertimeofday_Tick))
                print('\033[34m' + "Sent Time of Day to SSN-{}".format(self.node_select_radio_button.getSelectedNode()))
            elif message_id == SSN_MessageType_to_ID['GET_CONFIG']:
                print('\033[34m' + "Received GET_CONFIG from SSN-{}".format(node_index+1))

            # configs have been acknowledged?
            elif message_id == SSN_MessageType_to_ID['ACK_CONFIG']:
                configs_acknowledged = params[1]  # it is a list
                if configs_acknowledged == self.configs:
                    print('\033[34m' + "Received CONFIG ACK from SSN-{}".format(node_index + 1))
                    # self.config_button.config(bg='light green')
                    pass
                pass
            # status update message brings the ssn heartbeat status
            elif message_id == SSN_MessageType_to_ID['STATUS_UPDATE']:
                print('\033[34m' + "Received Status Update from SSN-{}".format(node_index+1))
                self.temperature_text[node_index].update(new_text_string=params[1])
                self.humidity_text[node_index].update(new_text_string=params[2])
                self.nodeuptime_text[node_index].update(new_text_string=self.servertimeofday_Tick-params[3])  # get the difference of static tick and current tick
                activity_level = SSN_ActivityLevelID_to_Type[params[4]]
                # get activity level of the SSN and display properly
                self.abnormalactivity_text[node_index].update(new_text_string=activity_level)
                if activity_level == 'NORMAL':
                    self.abnormalactivity_text[node_index].change_text_color(new_color='green')
                else:
                    self.abnormalactivity_text[node_index].change_text_color(new_color='red')
                machine_state_timestamps = []
                for i in range(4):
                    self.machine_loadcurrents[node_index][i].update(new_text_string=params[5+i])
                    self.machine_percentageloads[node_index][i].update(new_text_string=params[9+i])
                    self.machine_status[node_index][i].update(new_text_string=Machine_State_ID_to_State[params[13+i]])
                    state_timestamp_tick = params[17+i]
                    if state_timestamp_tick != 0:
                        # elapsed_time_in_state = self.servertimeofday_Tick - state_timestamp_tick
                        good_time = datetime.datetime.fromtimestamp(state_timestamp_tick)
                        exact_time_strings = ["{}:{}:{}".format(good_time.hour, good_time.minute, good_time.second), "{}/{}/{}".format(good_time.day, good_time.month, good_time.year)]
                    else:
                        # elapsed_time_in_state = state_timestamp_tick
                        exact_time_strings = ["0:0:0", "0/0/0"]
                    machine_state_timestamps.append(exact_time_strings)
                    self.machine_timeinstate[node_index][i].update(new_text_string=params[21+i])
                    self.machine_sincewheninstate[node_index][i].update(new_text_strings=machine_state_timestamps[i])
                    pass
                # append this data to our CSV file
                if self.csv_data_recording:
                    # insertiontimestamp, node_id, node_uptime, activitylevel,
                    # temperature, humidity,
                    # M1_load, M1_load%, M1_state, M1_statetimestamp, M1_stateduration,
                    # M2_*...
                    server_time_of_the_day = datetime.datetime.fromtimestamp(self.servertimeofday_Tick)
                    data_packet = [server_time_of_the_day, params[0], datetime.datetime.fromtimestamp(params[3]), activity_level,
                                   params[1], params[2],
                                   params[5], params[9], params[13], datetime.datetime.fromtimestamp(params[17]), params[21],
                                   params[6], params[10], params[14], datetime.datetime.fromtimestamp(params[18]), params[22]]
                    with open(self.csv_data_file+"-{}-{}-{}".format(server_time_of_the_day.day, server_time_of_the_day.month, server_time_of_the_day.year)+".csv",
                              'a', newline="") as f:
                        writer = csv.writer(f)
                        writer.writerow(data_packet)
                        pass
                    pass
                pass
            pass
        # recall this method after another second
        self.root_window.after(200, self.read_messages_and_update_UI)
        pass
    pass

