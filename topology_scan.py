from netifaces import interfaces, ifaddresses, AF_INET
import json
import os
import socket
import time
import socket
import fcntl
import struct
import ipaddress
import scapy.all as scapy 


#TODO
#No se si pueda hacer escacneo de router a router
#El SSH funciona a rudas, puede que limita el uso a ssh preconfigurado con comandos predeterminados
#no s si mi topologia sirva, de momento esta unicamente configurada con lo minimo en los routers, planeo implementar DHCP y routeo dinamico con rip
#La API esta en pañales, de momento no se ni coom funciona flask, tendre que aprender sobre la marcha
#Que mas queda? se debe de hacer ua presentacion en pttz- Eso deberia ser acil?

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
        #print(element[1].psrc + "      " + element[1].hwsrc)
        topology[socket.getfqdn(element[1].psrc)] = ({
                "IP":[element[1].psrc],
                "MAC":[element[1].hwsrc],
                "Subredes":[]
        })

    
    if bool(topology):
        j_topology = json.dumps(topology, indent=4)       
        return j_topology

def scan_all():
    ip=get_ip()
    return scan_topology_premade(ip)
    
def scan_routes():
    print("route")
    
print(scan_all())