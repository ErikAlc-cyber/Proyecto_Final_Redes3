from netifaces import interfaces, ifaddresses, AF_INET
import json
import os
import socket
import time
import fcntl
import struct
import ipaddress
import scapy.all as scapy 
import re
import ssher

def extract_network_info(config):
    network_info = []
    
    # Utiliza expresiones regulares para buscar direcciones IP y máscaras
    ip_pattern = r'ip address (\d+\.\d+\.\d+\.\d+) (\d+\.\d+\.\d+\.\d+)'
    
    matches = re.findall(ip_pattern, config)
    for match in matches:
        ip, mask = match
        network_info.append(f'{ip}/{mask}')
    
    return network_info

def get_ip():
    
    ip = [
        i['addr']
        for i in ifaddresses("tap0").setdefault(AF_INET, [{"addr": "No IP addr"}])
    ]
    dirty_ip = ip[0]
    
    ip = [
        i['netmask']
        for i in ifaddresses("tap0").setdefault(AF_INET, [{"addr": "No IP addr"}])
    ]
    dirty_mask = ip [0]

    network = ipaddress.IPv4Network(dirty_ip+"/"+dirty_mask, strict=False)
    return network

def scan_topology_premade(ip):
    topology = {}
    request = scapy.ARP() 
  
    request.pdst = str(ip)
    broadcast = scapy.Ether() 
  
    broadcast.dst = 'ff:ff:ff:ff:ff:ff'
  
    request_broadcast = broadcast / request 
    clients = scapy.srp(request_broadcast, timeout = 1)[0] 
    for element in clients: 
        topology[socket.getfqdn(element[1].psrc)] = ({
                "IP":[element[1].psrc],
                "MAC":[element[1].hwsrc],
                "Subredes":[str(ip)]
        })

    
    if bool(topology):
        return topology

def get_networks(ip):
    router_session=ssher.new_session(ip, "cisco", "root")
    i = 1
    router_session.retrieve_config("get_net.txt", i)

    with open(f'router_config-{i}.txt', 'r') as file:
        config_content = file.read()

    network_info = extract_network_info(config_content)
    return network_info


def scan_all():

    topology = {}
    root_ip=get_ip()
    networks = get_networks(str(root_ip.network_address + 1))
    
    for network_str in networks:
        network = ipaddress.IPv4Network(network_str, strict=False)
        topology[str(network)] = [
            scan_topology_premade(network)
        ]
    
    if bool(topology):
        out_file = open("devices.json", "w")
        j_topology = json.dump(topology, out_file, indent=4)
        out_file.close()       
    
    # Ahora topology contiene los resultados de todas las redes y subredes
    return topology

print(scan_all())