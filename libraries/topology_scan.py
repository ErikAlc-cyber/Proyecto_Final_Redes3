import pyshark
import json
import os
import socket
import time

def check_ping(ping_ip):
    """
    The function `check_ping` checks if a given IP address or hostname is reachable by sending a single
    ping request and returning `True` if the response is successful (0) and `False` otherwise.
    
    :param ping_ip: The `ping_ip` parameter is the IP address or hostname that you want to ping
    :return: the status of the ping. If the ping is successful (response code 0), it returns True.
    Otherwise, it returns False.
    """
    hostname = ping_ip
    response = os.system("fping -c 1 " + hostname)
    if response == 0:
        pingstatus = True
    else:
        pingstatus = False
    
    return pingstatus

def scan_topology_live(id_red, mascara):
    """
    The function `scan_topology` takes an IP address and a subnet mask as input, and scans the network
    topology by pinging each possible IP address within the given subnet range and retrieving the
    hostname for each reachable IP address.
    
    :param id_red: The parameter "id_red" represents the network ID or IP address of the network you
    want to scan. It should be in the format "x.x.x.x" where each "x" represents a number between 0 and
    255
    :param mascara: The "mascara" parameter represents the subnet mask of the network. It is used to
    determine the number of available IP addresses in the network
    """
    id_red_sep = id_red.split(".")
    id_red_separado = [ int(x) for x in id_red_sep ]
    possible_ip = 2 ** (32 - mascara) 
    topology = {}
    for i in range(possible_ip-1):
        
        id_red_separado[3] += 1
        
        if id_red_separado[3] > 255:
            id_red_separado[3] = 0
            id_red_separado[2] += 1
        
        elif id_red_separado[2] > 255:
            id_red_separado[1] += 1
        
        elif id_red_separado[1]> 255:
            print("Error")
            break
        
        new_ip = ".".join(str(element) for element in id_red_separado)
        print(new_ip) #Debug output
        
        if check_ping(new_ip):
            try:
                host_info = socket.gethostbyaddr(new_ip)
                hostname = host_info[0]
                topology[hostname] = new_ip
            except socket.herror:
                topology["Unknown host"] = new_ip

    if bool(topology):
        j_topology = json.dumps(topology, indent=4)       
        print(j_topology)

st = time.time()
scan_topology_live("10.25.200.0",24)
et = time.time()

# get the execution time
elapsed_time = et - st
print('Execution time:', elapsed_time, 'seconds')