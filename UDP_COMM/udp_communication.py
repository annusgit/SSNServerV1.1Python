
import select
from socket import *
import utils as utils
from Messages import *


class UDP_COMM:
    def __init__(self):
        # for multiple nodes
        self.SSN_Network_Address_Mapping = {}
        self.SSN_Network_Nodes = list()
        self.client_socket = None
        pass

    def __del__(self):
        # close the socket and delete it
        if self.client_socket is not None:
            self.client_socket.close()
        pass

    def udp_setup_connection(self, server_address, server_port):
        # create a udp socket and return
        self.client_socket = socket(family=AF_INET, type=SOCK_DGRAM)
        try:
            self.client_socket.bind((server_address, server_port))
        except:
            self.client_socket = None
            return None
        self.client_socket.setblocking(True)
        self.client_socket.settimeout(0.1)
        return True

    def decipher_node_message(self, node_message=None):
        # check message
        # for i in range(len(node_message)):
        #     print("{}, ".format(node_message[i]), end='')
        # message id and node id are always present in each message
        node_message_id = node_message[2]
        node_id = utils.get_MAC_id_from_bytes(high_byte=node_message[0], low_byte=node_message[1])

        # GET MAC message is received?
        if node_message_id == SSN_MessageType_to_ID['GET_MAC']:
            return node_message_id, [node_id]

        # Get configurations message is received?
        elif node_message_id == SSN_MessageType_to_ID['GET_CONFIG']:
            return node_message_id, [node_id]

        # acknowledge configurations message is received from the SSN?
        elif node_message_id == SSN_MessageType_to_ID['ACK_CONFIG']:
            configs_received = list()
            for i in range(4):
                configs_received.append(node_message[3+3*i])
                configs_received.append(node_message[4+3*i])
                configs_received.append(node_message[5+3*i])
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
            ssn_uptime = utils.get_int_from_bytes(highest_byte=node_message[56], higher_byte=node_message[57], high_byte=node_message[58], low_byte=node_message[59])
            abnormal_activity = node_message[60]
            # get machine specific information
            machine_load_currents, machine_load_percentages, machine_status, machine_state_timestamp, machine_state_duration = list(), list(), list(), list(), list()
            # print(node_message)
            for i in range(4):
                machine_load_currents.append(utils.get_word_from_bytes(high_byte=node_message[8+i*offset], low_byte=node_message[9+i*offset]) / 100.0)
                machine_load_percentages.append(node_message[10+i*offset])
                machine_status.append(node_message[11+i*offset])
                machine_state_timestamp.append(utils.get_int_from_bytes(highest_byte=node_message[12+i*offset], higher_byte=node_message[13+i*offset],
                                                                         high_byte=node_message[14+i*offset], low_byte=node_message[15+i*offset]))
                machine_state_duration.append(utils.get_int_from_bytes(highest_byte=node_message[16+i*offset], higher_byte=node_message[17+i*offset],
                                                                       high_byte=node_message[18+i*offset], low_byte=node_message[19+i*offset]))
                pass
            return node_message_id, [node_id, temperature, humidity, ssn_uptime, abnormal_activity, *machine_load_currents, *machine_load_percentages, *machine_status,
                                     *machine_state_timestamp, *machine_state_duration]
        return

    def read_udp_message(self):
        # check if we have incoming data or not, because we have a time out
        try:
            in_message, (self.node_ip, self.node_port) = self.client_socket.recvfrom(1024)
        except:
            return -1, -1, None
            pass
        # insert this into the SSN network dictionary
        # print(self.node_ip, self.node_port)
        message_id, params = self.decipher_node_message(in_message)
        node_MAC_id = params[0]
        if node_MAC_id not in self.SSN_Network_Address_Mapping:
            self.SSN_Network_Nodes.append(node_MAC_id)
            self.SSN_Network_Address_Mapping[node_MAC_id] = (self.node_ip, self.node_port)
            print('\033[32m' + "Added a new SSN into the network.")
            print('\033[32m' + "SSN-{} ({}): {} @ {}".format(len(self.SSN_Network_Address_Mapping), node_MAC_id, self.node_ip, self.node_port))
        # reset the IP and Port for this current node if it changed
        if node_MAC_id in self.SSN_Network_Address_Mapping.keys() and self.SSN_Network_Address_Mapping[node_MAC_id] != (self.node_ip, self.node_port):
            self.SSN_Network_Address_Mapping[node_MAC_id] = (self.node_ip, self.node_port)
            print('\033[32m' + "Updated SSN-{} ({}): {} @ {}".format(len(self.SSN_Network_Address_Mapping), node_MAC_id, self.node_ip, self.node_port))
        return self.SSN_Network_Nodes.index(node_MAC_id), message_id, params

    def udp_communication_test(self, server_address, server_port):
        client_socket = self.udp_setup_connection(server_address, server_port)
        while True:
            ready_to_read, ready_to_write, error = select.select([client_socket], [], [])
            if client_socket in ready_to_read:
                in_message, node_address = client_socket.recvfrom(100)
                out_message = self.decipher_node_message(in_message)
                print('\033[30m' + out_message)
            else:
                print('\033[30m' + "-> Nothing to read")
            pass
        pass

    def getNodeCountinNetwork(self):
        return len(self.SSN_Network_Address_Mapping)

    pass

    def send_set_mac_message(self, node_index, mac_address):
        set_mac_message = construct_set_mac_message(mac_address=mac_address)
        self.client_socket.sendto(set_mac_message, self.SSN_Network_Address_Mapping[self.SSN_Network_Nodes[node_index]])
        pass

    def send_set_timeofday_message(self, node_index, current_time):
        set_timeofday_message = construct_set_timeofday_message(current_time=current_time)
        self.client_socket.sendto(set_timeofday_message, self.SSN_Network_Address_Mapping[self.SSN_Network_Nodes[node_index]])
        pass

    def send_set_timeofday_Tick_message(self, node_index, current_tick):
        set_timeofday_message = construct_set_timeofday_Tick_message(current_Tick=current_tick)
        self.client_socket.sendto(set_timeofday_message, self.SSN_Network_Address_Mapping[self.SSN_Network_Nodes[node_index]])
        pass

    def send_set_config_message(self, node_index, config):
        set_config_message = construct_set_config_message(config=config)
        self.client_socket.sendto(set_config_message, self.SSN_Network_Address_Mapping[self.SSN_Network_Nodes[node_index]])
        pass

    def send_debug_reset_eeprom_message(self, node_index):
        debug_reset_eeprom_message = construct_debug_reset_eeprom_message()
        self.client_socket.sendto(debug_reset_eeprom_message, self.SSN_Network_Address_Mapping[self.SSN_Network_Nodes[node_index]])
        pass

    def send_debug_reset_ssn_message(self, node_index):
        debug_reset_ssn_message = construct_debug_reset_ssn_message()
        self.client_socket.sendto(debug_reset_ssn_message, self.SSN_Network_Address_Mapping[self.SSN_Network_Nodes[node_index]])
        pass
