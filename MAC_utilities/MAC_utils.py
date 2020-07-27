

def MAC_generator(start_address=0x0000, end_address=0xFFFF):
    mac_list = list()
    start = start_address
    while start <= end_address:
        mac_list.append(f"70:B3:D5:FE:{((start & 0xFF00) >> 8):02X}:{(start & 0x00FF):02X}\n")
        start += 1
    return mac_list


def generate_all_MAC_from_range(file_name="MAC.txt"):
    count = 0
    with open(file_name, "w") as mac_file:
        mac_list = MAC_generator(start_address=0x4CDF, end_address=0x4FFF)
        for mac_address in mac_list:
            mac_file.write(mac_address)
            count += 1
    print("LOG: Write Complete with {} MAC addresses".format(count))
    pass


def get_MAC_addresses_from_file(filename="None"):
    full_mac_list = list()
    with open(filename, "r") as mac_list:
        for mac_address in mac_list:
            full_mac_list.append(mac_address)
    return full_mac_list


def get_mac_bytes_from_mac_string(mac_address):
    # this function expects str('AA:BB:CC:DD:EE:FF')
    # and returns [0xAA, 0xBB, 0xCC, 0xDD, 0xEE, 0xFF]
    mac_in_bytes = list()
    for i in range(0, 18, 3):
        mac_in_bytes.append(int(mac_address[i:i+2], 16))
    return mac_in_bytes


