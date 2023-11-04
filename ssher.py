import paramiko
import time
import re

class ShellHandler:

    def __init__(self, host, user, psw):
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.ssh.connect(host, username=user, password=psw, port=22)

        channel = self.ssh.invoke_shell()
        self.stdin = channel.makefile('wb')
        self.stdout = channel.makefile('r')

    def __del__(self):
        self.ssh.close()

    def file_exec(self, commands):
        with open(commands, 'r') as f:
            comandos = [line for line in f.readlines()]
    
        for command in comandos:
            print("Hi")
             
    
 
def new_session(host, usr, password, flag):
    ssh_sesion = ShellHandler(host, usr, password)