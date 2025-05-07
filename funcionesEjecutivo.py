import json
import threading
from datetime import datetime
import funcionesCliente
from copy import deepcopy
mutex = threading.Lock()

def status(sock, onlineClients, incoming):
    with mutex:
        sock.sendall(f"Actualmente, hay {len(onlineClients)} en línea.".encode())
        if incoming:
            for client in range(len(incoming)):
                sock.sendall(f"Cliente {incoming[client][2]} está solicitando una conexión.".encode())
        else:
            sock.sendall("Por el momento, ningún cliente ha solicitado una conexión".encode())

def details(sock, filepathClientes, onlineClients):
    with mutex:
        n = len(onlineClients)
        with open(filepathClientes, "r") as file:
            data = json.load(file)
            for client in range(n):
                mail = onlineClients[client][1]
                hist = data[mail][2]
                if len(hist) == 0:
                    sock.sendall(f"Cliente {onlineClients[client][2]} - El cliente aún no ha realizado alguna acción.".encode())
                else:
                    sock.sendall(f"Cliente {onlineClients[client][2]} - Última acción: {funcionesCliente.translate(hist[-1]['tipo'])}, con fecha {funcionesCliente.dicttoDate(hist[-1]['fecha'])}".encode())
            file.close()

def catalogue(sock, filepath):
    with mutex:
        with open(filepath, "r") as file:
            data = json.load(file)
            for key, values in data.items():
                sock.sendall(f"[{key}] {values[0]} - Precio: {values[1]} - Stock {values[2]}".encode())
            file.close()

def history(sockCliente, filepathClientes, mailCliente):
    with mutex:
        with open(filepathClientes, "r") as file:
            data = json.load(file)
            hist = data[mailCliente][2]
            for action in range(len(hist)):
                if hist[action][1]["tipo"] == "compra" or hist[action][1]["tipo"] == "venta":
                    sockCliente.sendall(f"[{hist[action][0]}] {funcionesCliente.translate(hist[action][1]['tipo'])} - {hist[action][1]['nombre']} - Fecha: {funcionesCliente.dicttoDate(hist[action][1]['fecha'])} - Precio de compra / venta: {hist[action][1]['precio']}".encode())
                else:
                    sockCliente.sendall(f"[{hist[action][0]}] {funcionesCliente.translate(hist[action][1]['tipo'])} - {hist[action][1]['nombre']} - Fecha: {funcionesCliente.dicttoDate(hist[action][1]['fecha'])}".encode())
            file.close()

def buy(sockEjecutivo, filepathInventario, filepathClientes, cliente, articulo, precio):
    with mutex:
        with open(filepathClientes, "r+") as file1:
            data1 = json.load(file1)
            inv = data1[cliente[1]][3]
            if articulo in inv:
                if inv[articulo] != 0:
                    data1[cliente[1]][3][articulo] -= 1
                    data1[cliente[1]][2].append([len(data1[cliente[1]][2]) + 1, funcionesCliente.accion("venta", articulo, datetime.today(), precio)])
                    file1.seek(0)
                    json.dump(data1, file1, indent = 4)
                    file1.truncate()
                    file1.close()
                    with open(filepathInventario, "r+") as file2:
                        data2 = json.load(file2)
                        if articulo in data2:
                            data2[articulo] += 1
                        else:
                            data2[articulo] = 1
                        file2.seek(0)
                        json.dump(data2, file2, indent = 4)
                        file2.truncate()
                        file2.close()
                        print(f"[SERVIDOR]: Artículo '{articulo}' fue agregado al inventario sin publicar.")
                        sockEjecutivo.sendall(f"La compra de '{articulo}' se ha realizado con éxito.".encode())
                        cliente[0].sendall(f"La venta de '{articulo}' se ha realizado con éxito.".encode())
                else:
                    sockEjecutivo.sendall("El cliente no posee más unidades el artículo ingresado.".encode()) 
            else:
                sockEjecutivo.sendall("El cliente no posee el artículo ingresado.".encode())       

def publish(sockEjecutivo, carta, precio, filepathCatalogo, filepathInventario):
    """ Pone una carta a la venta por el precio del catalogo
    si no se tienen registros de esa carta se debe especificar un precio
    """
    with mutex:
        with open(filepathInventario, "r+") as file1:
            data1:dict = json.load(file1)
            if carta in data1:
                data1[carta] -= 1
                file1.seek(0)
                json.dump(data1, file1, indent = 4)
                file1.truncate()
                file1.close()
            else:
                sockEjecutivo.sendall("No hay existencias de la carta ingresada.".encode())
            with open(filepathCatalogo, "r+") as file2:
                data2 = json.load(file2)
                i = 0
                while i < len(data2):
                    key, value = data2.items()[i]
                    if value[0] == carta:
                        data2[key][2] += 1 # asumimos que si la carta/sobre ya está en el catálogo, se publica por su precio previamente definido 
                    i += 1
                if i == len(data2) - 1: # si llegamos al final del diccionario y la carta no existe (ej: el cliente vendió una carta sola), se crea una nueva entrada en el catálogo
                    data2[f"{len(data2) + 1}"] = [carta, precio, 1]
                file2.seek(0)
                json.dump(data2, file2, indent = 4)
                file2.truncate()
                file2.close()
                print(f"[SERVIDOR]: Una unidad de '{carta} fue agregada al catálogo'")
                sockEjecutivo.sendall(f"Artículo '{carta}' agregado exitosamente al catálogo.".encode())

def insert_dict(d,val):
    """inserta en la última posicion cierto valor
    """
    dcopy = deepcopy(d)
    dk = max(int(x) for x in dcopy.keys())
    nueva_clave = str(dk + 1)
    dcopy[nueva_clave] = val 

    return dcopy

def command_parser(sockEjecutivo, 
                   command, 
                   filepathArticulos, 
                   filepathInventario, 
                   admin, 
                   onlineClients, 
                   incoming, 
                   filepathClientes, 
                   sockCliente = None, 
                   mailCliente = None, 
                   connectionStatus = False):
    # si es comando, se llama a la función correspondiente; si no, se envía cómo mensaje al cliente:
        comm = command.split()
        instructions = comm[0]
        if instructions == ':status:':
            status(sockEjecutivo,onlineClients,incoming)
        elif instructions == ':details:':
            details(sockEjecutivo,filepathClientes,onlineClients)
        elif instructions == ':history:':
            if connectionStatus:
                history(sockCliente,filepathClientes,mailCliente)
            else:
                sockEjecutivo("Esta función sólo es válida en al estar conectado con un cliente.".encode())
        elif instructions == ':operations:':
            if connectionStatus:
                history(sockCliente,filepathClientes,mailCliente)
            else:
                sockEjecutivo("Esta función sólo es válida en al estar conectado con un cliente.".encode())
        elif instructions == ':catalogue:':
            catalogue(sockEjecutivo,filepathArticulos)
        elif instructions == ':buy':
            if connectionStatus:
                N = len(comm)
                if N != 3:
                    sockEjecutivo.sendall("Formato invalido. Recuerde que el formato es :buy <carta> <precio>:".encode())
                card = comm[1]
                price = int(comm[2].removesuffix(':'))
                buy(sockEjecutivo,filepathInventario,filepathClientes,sockCliente,card,price)
            else:
                sockEjecutivo("Esta función sólo es válida en al estar conectado con un cliente.".encode())
        elif instructions == ':publish':
            N = len(comm)
            card = comm[1]
            if N < 3:
                price = 0
            else:
                price = int(comm[2].removesuffix(':'))
            publish(sockEjecutivo, card, price, filepathArticulos, filepathInventario)
        elif instructions == ':exit:':
            sockEjecutivo.sendall("Nos vemos!".encode())
            admin.remove(sockEjecutivo)
            sockEjecutivo.close()
            pass
        else:
            if connectionStatus:
                sockCliente.sendall(f"[EJECUTIVO]: {command}".encode())
            else:
                pass
        sockEjecutivo.sendall("Ingresa un comando.".encode())


# TODO: programar las funciones disconnect y exit
# no has visto el video del woody 
# que está encima del auto de control remoto
# y tiene cara de volado y le hace un dap a 
# buzz lightyear
# lo has visto?

                
        