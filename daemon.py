import socket
import logging
import time
import json
import signal
import psutil
from daemonize import Daemonize

class App():
    def __init__(self):
        logger = logging.getLogger('syslog_parser')
        logger.setLevel(logging.INFO)

        formatter = logging.Formatter('%(levelname)s - %(message)s')

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        self.interval = 1
        self.shutdown_flag = False

        self.logger = logger

    def change_interval(self, number):
        self.interval = number

    def run(self):
        logs = {}
        logger = self.logger

        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_socket.bind(("0.0.0.0", 514))

        try:
            with open("logs.json", "w+") as out_file:
                while not self.shutdown_flag:
                    for _ in range((self.interval * 60) - 1):
                        data, addr = udp_socket.recvfrom(1024)
                        message = data.decode('utf-8')
                        print(f"Recibido desde {addr[0]}: {message}")
                        logs[time.time()] = {"log": f"Recibido desde {addr[0]}: {message}"}
                        time.sleep(1)

                    json.dump(logs, out_file, indent=4)
                    out_file.flush()
                    logs = {}  # Reinicia el diccionario después de escribir en el archivo

        except Exception as e:
            logger.error(f"Error: {e}")
        finally:
            udp_socket.close()

daemon = App()
daemon.run()