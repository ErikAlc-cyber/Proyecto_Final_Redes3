import paramiko
import re
import time
import socket
import json
import ipaddress
import netifaces
from socket import AF_INET
from ping3 import ping

topologia = {}
router = {} 

def obtener_router(Ip=None,name=None):
    """
    The function `obtener_router` retrieves information about a router from a JSON file based on either
    its IP address or name.
    
    :param Ip: The `Ip` parameter is used to specify the IP address of a router. If this parameter is
    provided, the function will return the information of the router with the specified IP address from
    the `routers_info.json` file
    :param name: The "name" parameter is used to specify the name of the router you want to obtain
    information for
    :return: the router information from the 'routers_info.json' file. If either the 'Ip' or 'name'
    parameter is provided, it will return the information for that specific router. If neither parameter
    is provided, it will return the information for all routers.
    """
    with open('routers_info.json') as archivo:
        datos = json.load(archivo)

        if Ip != None:
            router=datos[Ip]
        elif name != None:
            router=datos[name]
        else:
            return json.dumps(datos)
        
        return json.dumps(router)

# Función para obtener información de un dispositivo
def obtener_info_dispositivo(nombre, ip, usuario, contrasena):
    """
    The function `obtener_info_dispositivo` connects to a network device using SSH, retrieves its
    configuration information, and stores it in a dictionary.
    
    :param nombre: The name of the device you want to connect to
    :param ip: The "ip" parameter is the IP address of the device you want to connect to
    :param usuario: The parameter "usuario" is the username used to authenticate and connect to the
    device via SSH. It is typically a string value
    :param contrasena: The parameter "contrasena" is the password used to authenticate and establish a
    SSH connection with the device
    :return: nothing.
    """

    #if es_direccion_broadcast(ip):
        #print(f'La IP {ip} es la dirección de broadcast')
        #return

    if ping(ip) == None:
        print(f'La ip {ip} no existe o no se puede alcanzar')  
        return
    
    try:
        # Conéctate al dispositivo vía SSH
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ip, username=usuario, password=contrasena)

        # Abre un canal SSH
        canal = ssh.invoke_shell()

        # Envía comandos de inicio de sesión, si es necesario
        #canal.send('usuario\n')
        #canal.send('contrasena\n')

        # Desactiva la paginación
        canal.send('terminal length 0\n')

        # Agrega comandos adicionales si es necesario
        canal.send('enable\n')  # Ejemplo de comando 'enable' para privilegios ejecutivos
        time.sleep(2)        
        canal.send('root\n')  # Agrega comandos adicionales aquí
        time.sleep(2)
        # Espera un momento para que los comandos se ejecuten antes de obtener la salida
        while not canal.recv_ready():
            pass

        # Envía el comando 'show running-config' y obtiene la salida
        canal.send('show running-config\n')
        while not canal.recv_ready():
            pass
        time.sleep(5)
        configuracion = canal.recv(65535).decode('utf-8')

        nombre = (re.search(r'hostname\s+(\S+)', configuracion))
        nombre = nombre.group(1) if nombre else "Desconocido"
        ip_administrativa = re.search(r'ip address (\d+\.\d+\.\d+\.\d+)', configuracion)
        time.sleep(2)
        ip_administrativa = ip_administrativa.group(1) if ip_administrativa else "Desconocido"
        rol = re.search(r'role (\S+)', configuracion)
        rol = rol.group(1) if rol else "Desconocido"
        empresa = re.search(r'company (\S+)', configuracion)
        empresa = empresa.group(1) if empresa else "Desconocido"
        conexiones = re.findall(r'interface (\S+).*?ip address (\S+ \S+)', configuracion, re.DOTALL)

        canal.send("show version | include IOS\n")
        while not canal.recv_ready():
            pass
        time.sleep(5)
        configuracion = canal.recv(65535).decode('utf-8')
        sistema_operativo = re.search(r'Software \((.*?)\)', configuracion, re.IGNORECASE)
        sistema_operativo = sistema_operativo.group(0) if sistema_operativo else "Desconocido"

        canal.send("show ip interface brief\n")
        while not canal.recv_ready():
            pass
        time.sleep(5)
        configuracion = canal.recv(65535).decode('utf-8')
        ip_loopback = re.search(r'Loopback(\d+)\s+(\d+\.\d+\.\d+\.\d+)', configuracion)
        ip_loopback = ip_loopback.group(1) if ip_loopback else "Desconocido"

        router[ip] = {
            "Nombre": str(nombre),
            "IP Loopback": str(ip_loopback),
            "IP Administrativa": str(ip_administrativa),
            "Rol": str(rol),
            "Empresa": str(empresa),
            "Sistema Operativo": str(sistema_operativo),
            "Interfaces Activas": []
        }

        # Almacena la información en el diccionario de topología
        if ip not in topologia:
            topologia[ip] = {'ip': ip, 'conexiones': []}

        for conn in conexiones:
            interfaz = conn[0]
            direccion_ip = conn[1].split()[0]
            mascara = conn[1].split()[1]

            topologia[ip]['conexiones'].append({
                'interfaz': interfaz,
                'ip': direccion_ip,
                'mascara': mascara,
                'Liga': f'/routes/{ip}/{interfaz}'
            })

            router[ip]['Interfaces Activas'].append({
                'interfaz': interfaz,
                'ip': direccion_ip,
                'mascara': mascara
            })

        ssh.close()
        return
    
    except Exception as e:
        print(f"No se pudo conectar a router:{nombre} en {ip}: {str(e)}")


# Función para obtener información de un dispositivo
def obtener_interfaz(nombre, ip, usuario, contrasena):
    """
    The function `obtener_interfaz` connects to a device via SSH, sends commands to retrieve its
    interface configuration, and stores the information in a dictionary.
    
    :param nombre: The name of the device you want to obtain information from
    :param ip: The "ip" parameter is the IP address of the device you want to connect to
    :param usuario: The parameter "usuario" refers to the username used to connect to the device via
    SSH. It is the username that will be used to authenticate and establish the SSH connection
    :param contrasena: The parameter "contrasena" is the password used to authenticate and establish a
    connection to the device via SSH
    """
    interface = {}
    try:
        # Conéctate al dispositivo vía SSH
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ip, username=usuario, password=contrasena)

        # Abre un canal SSH
        canal = ssh.invoke_shell()

        # Envía comandos de inicio de sesión, si es necesario
        #canal.send('usuario\n')
        #canal.send('contrasena\n')

        # Desactiva la paginación
        canal.send('terminal length 0\n')

        # Agrega comandos adicionales si es necesario
        canal.send('enable\n')  # Ejemplo de comando 'enable' para privilegios ejecutivos
        time.sleep(2)        
        canal.send('root\n')  # Agrega comandos adicionales aquí
        time.sleep(2)
        # Espera un momento para que los comandos se ejecuten antes de obtener la salida
        while not canal.recv_ready():
            pass

        # Envía el comando 'show running-config' y obtiene la salida
        canal.send('show running-config\n')
        while not canal.recv_ready():
            pass
        time.sleep(5)
        configuracion = canal.recv(65535).decode('utf-8')
        time.sleep(2)

        # Analiza la configuración en busca de conexiones
        conexiones = re.findall(r'interface (\S+).*?ip address (\S+ \S+)', configuracion, re.DOTALL)
        time.sleep(3)

        # Almacena la información en el diccionario de topología
        
        for conn in conexiones:
            time.sleep(2)
            interface[conn[0]] = {
                'conexiones': [ 
                    {
                        'interfaz': conn[0],
                        'ip': conn[1],
                        'Estado': "No Activo" if ping(ip) == None else "Activo" , #Una funcion bien locochona
                        'Liga': f'/routes/{ip} *o* {nombre}/interfaces'
                    } 
                ]
            }

        ssh.close()

        if bool(interface):
            j_topology = json.dumps(interface)
            return j_topology

    except Exception as e:
        print(f"No se pudo conectar a {nombre} en {ip}: {str(e)}")

def incrementar_direccion_ip(ip):
    """
    The function takes an IP address as input and increments the last part of the address by 1.
    
    :param ip: The parameter `ip` is a string representing an IP address in the format "x.x.x.x", where
    each "x" represents a number between 0 and 255
    :return: the IP address with the last part incremented by 1.
    """
    partes_ip = ip.split('.')
    ultima_parte = int(partes_ip[-1])
    ultima_parte += 1
    partes_ip[-1] = str(ultima_parte)
    return '.'.join(partes_ip)

# Función para explorar la topología desde un router conocido
def explorar_topologia(desde_router, desde_ip, nivel=0, max_nivel=4, exploradas=set()):
    """
    The function `explorar_topologia` recursively explores a network topology starting from a given
    router and IP address, retrieving information about each device and its connections.
    
    :param desde_router: The starting router from where the topology exploration begins
    :param desde_ip: The starting IP address from where the topology exploration will begin
    :param nivel: The "nivel" parameter represents the current level of depth in the topology
    exploration. It starts at 0 and increases by 1 with each recursive call, defaults to 0 (optional)
    :param max_nivel: The parameter "max_nivel" represents the maximum level of depth or hierarchy that
    the function will explore in the topology. It determines how many levels of connections will be
    traversed from the starting router, defaults to 3 (optional)
    :return: nothing (None).
    """
    if nivel > max_nivel or desde_ip in exploradas:
        return

    obtener_info_dispositivo(desde_router, desde_ip, 'cisco', 'root')  # Reemplaza con tus credenciales
    exploradas.add(desde_ip)

    if desde_router in topologia:
        for conn in topologia[desde_router]['conexiones']:
            nuevo_router = conn['ip'].split()[0]
            nueva_ip = conn['ip'].split()[0]
            if nuevo_router not in topologia:
                explorar_topologia(nuevo_router, nueva_ip, nivel, max_nivel, exploradas)
            else:
                explorar_topologia(incrementar_direccion_ip(nuevo_router), incrementar_direccion_ip(nueva_ip), nivel + 1, max_nivel, exploradas)

def get_ip():
    """
    The function `get_ip` retrieves the IP address and netmask of the "tap0" interface and returns the
    corresponding network.
    :return: an IPv4 network object.
    """
    
    ip = [
        i['addr']
        for i in netifaces.ifaddresses("tap0").setdefault(AF_INET, [{"addr": "No IP addr"}])
    ]
    dirty_ip = ip[0]
    
    ip = [
        i['netmask']
        for i in netifaces.ifaddresses("tap0").setdefault(AF_INET, [{"addr": "No IP addr"}])
    ]
    dirty_mask = ip [0]

    network = ipaddress.IPv4Network(dirty_ip+"/"+dirty_mask, strict=False)
    
    return network.network_address


def scan_all():
    """
    The function `scan_all` scans the network topology starting from a known router and saves the
    results in a JSON file.
    :return: the topology dictionary, which contains information about the network devices and their
    connections.
    """
    
    # Define el router inicial y su dirección IP (Se hace en automatico)
    red_inicial = str(get_ip())
    primer_ip = incrementar_direccion_ip(red_inicial)
    
    router_inicial = primer_ip
    ip_router_inicial = primer_ip

    # Comienza a explorar la topología desde el router conocido
    explorar_topologia(router_inicial, ip_router_inicial)

    # Imprime la topología al final
    topology = {}

    for dispositivo, info in topologia.items(): 
        
        topology[socket.getfqdn(info['ip'])] = ({
                "IP":[info['ip']],
                "Subredes":[
                {
                     conn['interfaz']: {
                        'ip': conn['ip'],
                        'mascara': conn['mascara']
                    }
                } for conn in info['conexiones']]
        })

    if bool(topology):

        #Info gral. topologia
        out_file = open("new-devices.json", "w")
        j_topology = json.dumps(topology)
        out_file.write(j_topology)
        out_file.close()  
        
        #Info especifica por router
        out_file = open("routers_info.json", "w")
        routers_info = json.dumps(router)
        out_file.write(routers_info)
        out_file.close()

        return j_topology
    
    return None

print(type(obtener_router()))