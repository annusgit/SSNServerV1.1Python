from MAC_utilities import get_mac_bytes_from_mac_string

SSN_MessageType_to_ID = {
    'GET_MAC':               1,
    'SET_MAC':               2,
    'GET_TIMEOFDAY':         3,
    'SET_TIMEOFDAY':         4,
    'GET_CONFIG':            5,
    'SET_CONFIG':            6,
    'ACK_CONFIG':            7,
    'STATUS_UPDATE':         8,
    'RESET_MACHINE_TIME':    9,
    'DEBUG_EEPROM_CLEAR':   10,
    'DEBUG_RESET_SSN':      11
}

SSN_MessageID_to_Type = {x:y for y,x in SSN_MessageType_to_ID.items()}
SSN_ActivityLevelID_to_Type = {0: 'NORMAL', 1: 'ABNORMAL', 2: 'TREADFAIL', 3: 'TCOMMFAIL'}
offset = 12


def construct_set_mac_message(mac_address):
    mac_address_in_bytes = get_mac_bytes_from_mac_string(mac_address=mac_address)
    set_mac_message = [SSN_MessageType_to_ID['SET_MAC'], *mac_address_in_bytes]
    return bytearray(set_mac_message)


def construct_set_timeofday_message(current_time):
    set_timeofday_message = [SSN_MessageType_to_ID['SET_TIMEOFDAY'], int(current_time.hour), int(current_time.minute), int(current_time.second),
                             int(current_time.day), int(current_time.month), int(current_time.year - 2000)]
    return bytearray(set_timeofday_message)


def construct_set_timeofday_Tick_message(current_Tick):
    set_timeofday_Tick_message = [SSN_MessageType_to_ID['SET_TIMEOFDAY'], current_Tick[0], current_Tick[1], current_Tick[2], current_Tick[3]]
    return bytearray(set_timeofday_Tick_message)


def construct_set_config_message(config):
    set_config_message = [SSN_MessageType_to_ID['SET_CONFIG'], *config]
    return bytearray(set_config_message)


def construct_debug_reset_eeprom_message():
    debug_reset_eeprom_message = [SSN_MessageType_to_ID['DEBUG_EEPROM_CLEAR']]
    return bytearray(debug_reset_eeprom_message)


def construct_debug_reset_ssn_message():
    debug_reset_ssn_message = [SSN_MessageType_to_ID['DEBUG_RESET_SSN']]
    return bytearray(debug_reset_ssn_message)



