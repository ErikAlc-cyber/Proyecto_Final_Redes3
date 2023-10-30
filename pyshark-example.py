import pyshark
import tkinter as tk
from tkinter import filedialog
import sys
from os import system
import psutil
import os
import platform

def limpiar_consola():
    sistema_operativo = platform.system()
    if sistema_operativo == "Windows":
        os.system("cls")
    else:
        os.system("clear")

def listar_adaptadores_de_red():
    adaptadores_de_red = psutil.net_if_addrs()
    print("Lista de adaptadores de red disponibles:")
    
    for i, adaptador in enumerate(adaptadores_de_red, start=1):
        print(f"{i}. {adaptador}")
    
    while True:
        try:
            opcion = int(input("Por favor, elige un adaptador (1-{}): ".format(len(adaptadores_de_red))))
            if 1 <= opcion <= len(adaptadores_de_red):
                adaptador_elegido = list(adaptadores_de_red.keys())[opcion - 1]
                return adaptador_elegido
            else:
                print("Opción no válida. Por favor, elige un número entre 1 y {}.".format(len(adaptadores_de_red)))
        
        except ValueError:
            print("Entrada no válida. Por favor, ingresa un número válido.")

def display_menu(menu):
    """
    Display a menu where the key identifies the name of a function.
    :param menu: dictionary, key identifies a value which is a function name
    :return:
    """
    for k, function in menu.items():
        print(k, function.__name__)


def pcap_file():
    """
    The function `pcap_file()` opens a file dialog to select a pcap or cap file, then uses pyshark to
    capture and print the contents of the selected file.
    """
    limpiar_consola()    
    filetypes = (
        ('Capture files', '*.pcap, *.cap, *.pcapng'),
        ('All files', '*.*')
    )
    
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(
        title='Open a file',
        initialdir='/',
        filetypes=filetypes)
    
    cap = pyshark.FileCapture(file_path, tshark_path="h:\Wireshark\\tshark.exe")
    print(cap[0])
    
def print_callback(pkt):
    print ('Llego: {}'.format(pkt))
    
def live_capture():
    limpiar_consola()
    inter = listar_adaptadores_de_red()
    limpiar_consola()
    capture = pyshark.LiveCapture(interface=inter, tshark_path="h:\Wireshark\\tshark.exe")
    capture.apply_on_packets(print_callback, timeout=5)

def fin():
    """
    The `fin()` function clears the standard output and prints "Adios" before exiting the program.
    """
    limpiar_consola()
    print("Adios")
    sys.exit()


def main():
    """
    The main function creates a menu dictionary and allows the user to select and call functions based
    on their input.
    """
    # Create a menu dictionary where the key is an integer number and the
    # value is a function name.
    functions_names = [pcap_file, live_capture, fin]
    menu_items = dict(enumerate(functions_names, start=1))

    while True:
        display_menu(menu_items)
        selection = int(
            input("Selecciona una opcion: "))  # Get function key
        selected_value = menu_items[selection]  # Gets the function name
        selected_value()  # add parentheses to call the function

if __name__ == '__main__':
    main()