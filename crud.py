import paramiko
import re
import time
import socket
import json

class usr_router:
    def __init__(self, name, permit, device) -> None:
        self.nombre = name
        self.permisos = permit
        self.dispositivo = device

def obtener_usuarios(nombre, ip, usuario, contrasena):
    """
    The function `obtener_usuarios` connects to a device via SSH, sends commands to retrieve its
    users, and stores the information in a dictionary.
    
    :param nombre: The name of the device you want to obtain information from
    :param ip: The "ip" parameter is the IP address of the device you want to connect to
    :param usuario: The parameter "usuario" refers to the username used to connect to the device via
    SSH. It is the username that will be used to authenticate and establish the SSH connection
    :param contrasena: The parameter "contrasena" is the password used to authenticate and establish a
    connection to the device via SSH
    """
    usuario = {}
    try:
        # Conéctate al dispositivo vía SSH
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ip, username=usuario, password=contrasena)

        # Abre un canal SSH
        canal = ssh.invoke_shell()

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
        usuarios = re.findall(r'username (\S+).*?', configuracion, re.DOTALL)
        time.sleep(3)

        # Almacena la información en el diccionario de topología
        for usr in usuarios:
            time.sleep(2)
            usuarios[nombre] = {
                'Usuariois': usr[0],
            }

        # Almacena la información en el diccionario de topología
        ssh.close()
        return json.dumps(usuarios,indent=4)

    except Exception as e:
        print(f"No se pudo conectar a {nombre} en {ip}: {str(e)}")
