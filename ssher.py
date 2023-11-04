import paramiko
import time
import re
import time
import json

class ShellHandler:

    def __init__(self, host, user, psw):
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.ssh.connect(host, username=user, password=psw, port=22)

    def __del__(self):
        self.ssh.close()

    def retrieve_config(self):
        stdin, stdout, stderr = self.ssh.exec_command("show running-config")
        router_config = stdout.read().decode('utf-8')

        # Guarda la configuración en un archivo
        with open("router_config.txt", "w") as config_file:
            config_file.write(router_config)
    
    def exec_commands(self, comands):
        
        new_conn = self.ssh.invoke_shell()
        
        with open(comands, 'r') as f:
            comandos = [line for line in f.readlines()]
        
        for comando in comandos:
            new_conn.send(comando)
            time.sleep(2)
            salida = nueva_conexion.recv(max_buffer)
            
def new_session(host, usr, password):
    ssh_sesion = ShellHandler(host, usr, password)