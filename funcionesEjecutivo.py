import socket
import json
import sys
import threading
from datetime import datetime
import funcionesCliente
mutex = threading.Lock()

def status(sock, onlineClients, incoming):
    with mutex:
        sock.sendall(f"Actualmente, hay {len(onlineClients)} en línea.")
        if incoming:
            for client in range(len(incoming)):
                sock.sendall(f"Cliente {incoming[client]} está solicitando una conexión.")
        else:
            sock.sendall("Por el momento, ningún cliente ha solicitado una conexión")

def details(sock, filepath, onlineClients):
    with mutex:
        n = len(onlineClients)
        with open(filepath, "r") as file:
            data = json.load(file)
            for client in range(n):
                mail = onlineClients[client][1]
                sock.sendall(f"Cliente {onlineClients[client][2]} - Última acción: {funcionesCliente.translate(data[mail][2][-1]["tipo"])}, con fecha {funcionesCliente.dicttoDate(data[mail][2][-1]["fecha"])}")
            file.close()

def catalogue(sock, filepath):
    with mutex:
        with open(filepath, "r") as file:
            data = json.load(file)
            for key, values in data.items():
                sock.sendall(f"[{key}] {values[0]} - Precio: {values[1]} - Stock {values[2]}")
            file.close()

def history(filepathCliente, sockCliente, mailCliente):
    with mutex:
        with open(filepathCliente, "r") as file:
            data = json.load(file)
            hist = data[mailCliente][2]
            for action in range(len(hist)):
                if hist[action][1]["tipo"] == "compra" or hist[action][1]["tipo"] == "venta":
                    sockCliente.sendall(f"[{hist[action][0]}] {funcionesCliente.translate(hist[action][1]["tipo"])} - {hist[action][1]["nombre"]} - Fecha: {funcionesCliente.dicttoDate(hist[action][1]["fecha"])} - Precio de compra / venta: {hist[action][1]["precio"]}")
                else:
                    sockCliente.sendall(f"[{hist[action][0]}] {funcionesCliente.translate(hist[action][1]["tipo"])} - {hist[action][1]["nombre"]} - Fecha: {funcionesCliente.dicttoDate(hist[action][1]["fecha"])}")
                    
def 
