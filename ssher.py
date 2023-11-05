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

    def clear_buffer(self,conexion):
        max_buffer = 1000000000000000000000000000000000
        if conexion.recv_ready():
            return conexion.recv(max_buffer)

    def retrieve_config(self, comands, i):

        max_buffer = 2**63 - 1

        new_conn = self.ssh.invoke_shell()
        salida = self.clear_buffer(new_conn)
        time.sleep(2)
        new_conn.send("terminal length 0\n")
        salida = self.clear_buffer(new_conn)

        with open(comands, 'r') as f:
            comandos = [line for line in f.readlines()]

        with open(f"router_config-{i}.txt", "w") as t:
            for comando in comandos:
                new_conn.send(comando)
                time.sleep(2)
                router_config = new_conn.recv(max_buffer)
                print(f'{router_config}')
                t.write(str(router_config))

    def exec_commands(self, comands):
        
        max_buffer = 65535
        new_conn = self.ssh.invoke_shell()
        salida = self.clear_buffer(new_conn)
        time.sleep(2)
        new_conn.send("terminal length 0\n")
        
        with open(comands, 'r') as f:
            comandos = [line for line in f.readlines()]
        
        for comando in comandos:
            new_conn.send(comando)
            time.sleep(2)
            salida = new_conn.recv(max_buffer)

def new_session(host, usr, password):
    ssh_sesion = ShellHandler(host, usr, password)
    return ssh_sesion