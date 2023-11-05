import paramiko
import re
import time
import socket
import json

# Diccionario para almacenar la información de los dispositivos y sus conexiones
topologia = {}

# Función para obtener información de un dispositivo
def obtener_info_dispositivo(nombre, ip, usuario, contrasena):
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
            topologia[nombre] = {
                'ip': ip,
                'conexiones': [ 
                    {
                        'interfaz': conn[0], 'ip': conn[1]
                    } 
                ]
            }

        ssh.close()

    except Exception as e:
        print(f"No se pudo conectar a {nombre} en {ip}: {str(e)}")

def incrementar_direccion_ip(ip):
    partes_ip = ip.split('.')
    ultima_parte = int(partes_ip[-1])
    ultima_parte += 1
    partes_ip[-1] = str(ultima_parte)
    return '.'.join(partes_ip)

# Función para explorar la topología desde un router conocido
def explorar_topologia(desde_router, desde_ip, nivel=0, max_nivel=3):
    if nivel > max_nivel:
        return
    obtener_info_dispositivo(desde_router, desde_ip, 'cisco', 'root')  # Reemplaza con tus credenciales
    if desde_router in topologia:
        for conn in topologia[desde_router]['conexiones']:
            nuevo_router = conn['ip'].split()[0]
            nueva_ip = conn['ip'].split()[0]
            if nuevo_router not in topologia:
                explorar_topologia(nuevo_router, nueva_ip, nivel, max_nivel)
            else:
                explorar_topologia(nuevo_router, incrementar_direccion_ip(nueva_ip), nivel + 1, max_nivel)

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


def scan_all():
    
    # Define el router inicial y su dirección IP (debes ajustarlo según tu red)
    router_inicial = 'real_world'
    ip_router_inicial = '192.168.200.1'

    # Comienza a explorar la topología desde el router conocido
    explorar_topologia(router_inicial, ip_router_inicial)

    # Imprime la topología al final
    topology = {}

    for dispositivo, info in topologia.items(): 
        
        topology[socket.getfqdn(info['ip'])] = ({
                "IP":[info['ip']],
                "Subredes":[
                {
                    conn['interfaz']: conn['ip']
                } for conn in info['conexiones']]
        })

    if bool(topology):
        out_file = open("new-devices.json", "w")
        j_topology = json.dump(topology, out_file, indent=4)
        out_file.close()  
    print("Completado!")
    return topology

print(scan_all())