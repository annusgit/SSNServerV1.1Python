import paho.mqtt.client as mqtt
from queue import Queue
from Messages import *
import utils as utils


class MQTT:
    def __init__(self, client_id, host, port=1883, keep_alive=60):
        self.client = mqtt.Client(client_id=client_id)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.host, self.port, self.keep_alive = host, port, keep_alive
        self.client.connect(host, port, keep_alive)
        self.message_queue = Queue()
        # for multiple nodes
        self.SSN_Network_Address_Mapping = {}
        self.SSN_Network_Nodes = list()
        pass

    # The callback for when the client receives a CONNACK response from the server.
    def on_connect(self, client, userdata, flags, rc):
        print("Connected with result code " + str(rc))
        # Subscribing in on_connect() means that if we lose the connection and
        # reconnect then subscriptions will be renewed.
        # this is our status update channel for all nodes
        client.subscribe("/SSN/")
        pass

    # The callback for when a PUBLISH message is received from the server.
    def on_message(self, _, __, in_message):
        # print(f"{msg.topic}: {msg.payload.decode('utf-8')}")
        # print(in_message.payload, in_message.qos, in_message.topic, in_message.retain)
        message_id, params = self.decipher_node_message(in_message.payload)
        node_MAC_id = params[0]
        if node_MAC_id not in self.SSN_Network_Nodes:
            self.SSN_Network_Nodes.append(node_MAC_id)
            print('\033[32m' + "Added a new SSN into the network.")
            print('\033[32m' + "SSN-{} ({})".format(len(self.SSN_Network_Address_Mapping), node_MAC_id))
            pass
        self.message_queue.put([self.SSN_Network_Nodes.index(node_MAC_id), message_id, params])

    def decipher_node_message(self, node_message=None):
        # message id and node id are always present in each message
        node_id = utils.get_MAC_id_from_bytes(high_byte=node_message[0], low_byte=node_message[1])
        node_message_id = node_message[2]

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
            print(state_flags)
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

    def send_set_mac_message(self, mac_address):
        set_mac_message = construct_set_mac_message(mac_address=mac_address)
        self.client.publish(topic="/SSN/CONFIG", payload=set_mac_message)
        pass

    def send_set_timeofday_message(self, current_time):
        set_timeofday_message = construct_set_timeofday_message(current_time=current_time)
        self.client.publish(topic="/SSN/CONFIG", payload=set_timeofday_message)
        pass

    def send_set_timeofday_Tick_message(self, current_tick):
        set_timeofday_message = construct_set_timeofday_Tick_message(current_Tick=current_tick)
        self.client.publish(topic="/SSN/CONFIG", payload=set_timeofday_message)
        pass

    def send_set_config_message(self, config):
        set_config_message = construct_set_config_message(config=config)
        self.client.publish(topic="/SSN/CONFIG", payload=set_config_message)
        pass

    def send_debug_reset_eeprom_message(self):
        debug_reset_eeprom_message = construct_debug_reset_eeprom_message()
        self.client.publish(topic="/SSN/CONFIG", payload=debug_reset_eeprom_message)
        pass

    def send_debug_reset_ssn_message(self):
        debug_reset_ssn_message = construct_debug_reset_ssn_message()
        self.client.publish(topic="/SSN/CONFIG", payload=debug_reset_ssn_message)
        pass

    pass
