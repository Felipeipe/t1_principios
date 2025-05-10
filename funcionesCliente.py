import socket
import json
import sys
import threading
from datetime import datetime

def datetoDict(date):
    return {"año":date.year, "mes":date.month, "dia":date.day, "hora":date.time().hour, "minuto":date.time().minute, "segundo":date.time().second}

def dicttoDate(dict):
    return datetime(dict["año"], dict["mes"], dict["dia"], dict["hora"], dict["minuto"], dict["segundo"])


class accion:
    def __init__(self, type: str, name = "a", date = datetime.today(), price = 0, recv = False, dev = False):
        assert type == "compra" or type == "venta" or type == "cambio" or type == "confirm" or type == "devo" or type == "hist" or type == "exec"
        self.type = type
        self.name = name
        self.date = date
        self.price = price
        self.recv = recv
        self.dev = dev

    def changeRecv(self):
        self.recv = not self.recv

    def changeDev(self):
        self.dev = not self.dev

    def asdict(self):
        
        if self.type == "compra":
            return {"tipo":self.type, "nombre":self.name, "fecha":datetoDict(self.date), "precio":self.price, "recib":self.recv, "devo":self.dev}
        elif self.type == "venta":
            return {"tipo":self.type, "nombre":self.name, "fecha":datetoDict(self.date), "precio":self.price}
        elif self.type == "confirm" or self.type == "devo":
            return {"tipo":self.type, "nombre":self.name, "fecha":datetoDict(self.date)}
        else:
            return {"tipo":self.type, "fecha":datetoDict(self.date)}
        
def logic(boolean_val):
    if boolean_val:
        return 1
    else:
        return 0
    
def translate(x):
    assert type(x) == str
    if x == "compra":
        return "Compra de artículo"
    elif x == "venta":
        return "Venta de artículo"
    elif x == "cambio":
        return "Cambio de contraseña"
    elif x == "confirm":
        return "Confirmación de envío"
    elif x == "devo":
        return "Reembolso de artículo"
    elif x == "hist":
        return "Revisión de historial"
    elif x == "exec":
        return "Conexión con ejecutivo"

mutex = threading.Lock() 

def cambioContraseña(sock:socket.socket, filepath:str, mail: str): 
    """Cambiar la contraseña actual de un usuario"""
    while True:
        sock.sendall("Ingrese su contraseña actual. Si no desea cambiar su contraseña escriba :cancel: \n".encode())
        act = sock.recv(1024).decode()
        if act == ':cancel:':
            sock.sendall("Volviendo al menú principal...\n".encode())
            break
        with mutex:
            with open(filepath, "r+") as file: # se abre el archivo asociado a los clientes
                data = json.load(file)
        if act == data[mail][0]: # si la contraseña ingresada coincide con la registrada...
            while True:
                sock.sendall("Ingrese su nueva contraseña: \n".encode()) 
                new = sock.recv(1024).decode() # se recibe la contraseña nueva
                if new == ':cancel:':
                    sock.sendall("Volviendo al menú principal...\n".encode())
                    break
                sock.sendall("Repita su nueva contraseña: \n".encode())
                newRep = sock.recv(1024).decode() # se recibe una confirmación de la contraseña nueva
                if newRep == ':cancel:':
                    sock.sendall("Volviendo al menú principal...\n".encode())
                    break
                if new == newRep: # si las contraseñas coinciden...
                    with mutex:
                        with open(filepath, "r+") as file:
                            data[mail][0] = new # se setea la contraseña ingresada cómo la nueva contraseña
                            data[mail][2].append([len(data[mail][2]) + 1, accion("cambio").asdict()]) # se guarda la acción en el historial
                            file.seek(0)
                            json.dump(data, file, indent = 4)
                            file.truncate()
                            sock.sendall("Contraseña cambiada con éxito!\n".encode())
                            print(f"[SERVIDOR]: Cambio de clave - Cliente {data[mail][1]}\n")
                            break
                else:
                    sock.sendall("Las contraseñas no coinciden, intente nuevamente.\n".encode()) # si la nueva contraseña y su confirmación no coincide
            break
        else:
            sock.sendall("Contraseña incorrecta, intente nuevamente.\n".encode()) # si la contraseña ingresada no coincide con la registrada en la base de datos

def catalogoCompra(sock:socket.socket, filepath1: str, filepath2: str, mail: str): 
    """ver el catálogo de la tienda y permitir 
    comprar artículos (se podría agregar comprar más de una unidad por acción)"""
    while True:
        with mutex:
            with open(filepath1, "r+") as file1: # se abre el archivo articulos.json con los artículos
                data1 = json.load(file1)
        for key, value in data1.items():
            sock.sendall(f"[{key}] {value[0].replace('_', ' ')} - ${value[1]}\n".encode()) # se muestran los elementos del catálogo
        sock.sendall("¿Desea comprar algún elemento del catálogo? Ingrese un número (0 = Salir)\n".encode())
        ans = sock.recv(1024).decode()
        if ans == '0': # salir del catálogo sin comprar nada
            break
        elif ans.isnumeric() and 0 < int(ans) < len(data1) + 1: # si el artículo es válido...
            sock.sendall(f"Confirme la compra de '{data1[ans][0].replace('_', ' ').lower()}' por {data1[ans][1]} (1 = Confirmar - 0 = Cancelar)\n".encode())
            conf = sock.recv(1024).decode()
            if conf == "1": # si se confirma la compra...
                if data1[ans][2] > 0: # si hay stock...
                    with mutex:                          
                        with open(filepath2, "r+") as file2: # se abre el archivo asociado a los clientes
                            data2 = json.load(file2)
                            data2[mail][2].append([len(data2[mail][2]) + 1, accion("compra", str(data1[ans][0]), datetime.today(), data1[ans][1]).asdict()]) # se guarda la compra en el historial del cliente
                            file2.seek(0)
                            json.dump(data2, file2, indent = 4)
                            file2.truncate()
                        data1[ans][2] -= 1 # se reduce el stock luego de la compra
                        with open(filepath1, "r+") as file1:
                            file1.seek(0)
                            json.dump(data1, file1)
                            file1.truncate()
                        sock.sendall("Compra realizada con éxito!\n".encode())
                        print(f"[SERVIDOR] Cliente {data2[mail][1]} ha comprado {data1[ans][0]} por {data1[ans][1]}\n")
                        break
                else:
                    sock.sendall("No hay stock del artículo seleccionado. Lo sentimos \n".encode()) # no hay stock
            elif conf == "0":
                sock.sendall("Compra cancelada.\n".encode()) # no se confirma la compra del artículo
                sock.sendall("¿Se te ofrece algo más?\n".encode())
            else:
                sock.sendall("Ingrese una respuesta válida.\n".encode()) # se ingresa una respuesta inválida al confirmar la compra
        else:
            sock.sendall("Ingrese un artículo válido.\n".encode()) # se ingresa una id inválida al elegir un artículo

def verHistorial(sock:socket.socket, filepath, mail):
    while True:
        with mutex:
            with open(filepath, "r") as file:
                data = json.load(file)
        hist = data[mail][2]
        today = datetime.today()
        n = 1
        transactions = []
        if len(hist) < 1:
            sock.sendall("Usted no ha realizado transacciones.".encode())
            break
        else:
            for i in range(len(hist)):
                actDate = dicttoDate(hist[i][1]["fecha"])
                if (today - actDate).days <= 365 and (hist[i][1]["tipo"] == "compra" or hist[i][1]["tipo"] == "venta"):
                    transactions.append(hist[i][1])
                    sock.sendall(f"[{n}] {actDate.year}-{actDate.month}-{actDate.day}\n".encode())
                    n += 1
            data[mail][2].append([len(data[mail][2]) + 1, accion("hist").asdict()])
            with mutex:
                with open(filepath, "r+") as file:
                    file.seek(0)
                    json.dump(data, file, indent = 4)
                    file.truncate()
            sock.sendall("\n¿Desea más información sobre alguna transacción? Ingrese un número (0 = Salir)\n".encode())
            ans = sock.recv(1024).decode()
            if ans == "0":
                break
            elif ans.isnumeric() and 0 < int(ans) < n: 
                ans = int(ans)
                sock.sendall("Datos:\n".encode())
                sock.sendall(f"Tipo - {translate(transactions[ans - 1]['tipo'])}\n".encode())                   
                sock.sendall(f"Fecha - {dicttoDate(transactions[ans - 1]['fecha'])}\n".encode())
                sock.sendall(f"Artículo - {transactions[ans - 1]['nombre'].replace('_', ' ')}\n".encode())
                sock.sendall(f"Precio - {transactions[ans - 1]['precio']}\n".encode())
                if transactions[ans - 1]["tipo"] == "compra":
                    sock.sendall(f"El artículo ha sido pagado{logic(not transactions[ans - 1]['recib'])*' y está en camino.'}{logic(transactions[ans - 1]['recib'])*', su envío fue confirmado'}{logic(transactions[ans - 1]['devo'])*', y se ha tramitado su devolución.'}\n".encode())
                break
            else:
                sock.sendall("Ingresa una respuesta válida.".encode())

def confirmarEnvio(sock:socket.socket, filepath, mail):
    while True: 
        with mutex:
            with open(filepath, "r+") as file:
                data = json.load(file)
        hist = data[mail][2]
        today = datetime.today()
        transactions = []
        n = 1
        for i in range(len(hist)):
            actDate = dicttoDate(hist[i][1]["fecha"])
            if (today - actDate).days <= 365 and hist[i][1]["tipo"] == "compra" and hist[i][1]["recib"] == False:
                transactions.append(hist[i])
                sock.sendall(f"[{n}] {hist[i][1]['nombre'].replace('_', ' ')} | {actDate.year}-{actDate.month}-{actDate.day}\n".encode())
                n += 1
        if transactions == []:
            sock.sendall("No hay transacciones que requieran confirmar envío.\n".encode())
            break
        else:
            sock.sendall("\n¿Cual de los artículos anteriores recibiste? (0 = Salir)\n".encode())
            ans = sock.recv(1024).decode()
            if ans  == "0":
                break
            elif ans.isnumeric() and 0 < int(ans) < n:
                ans = int(ans)
                sock.sendall(f"¿Deseas confirmar que el envío de '{transactions[ans - 1][1]['nombre'].replace('_', ' ')}' se concretó de forma exitosa? (1 = Aceptar - 0 = Cancelar)\n".encode())
                resp = sock.recv(1024).decode()
                if resp == "0":
                    sock.sendall("Acción cancelada.\n".encode())
                    break
                elif resp == "1":
                    data[mail][2][transactions[ans - 1][0] - 1][1]["recib"] = True
                    data[mail][2].append([len(data[mail][2]) + 1, accion("confirm", f"{transactions[ans - 1][1]['nombre']} (Comprado el {dicttoDate(transactions[ans - 1][1]['fecha'])})").asdict()])
                    name = transactions[ans - 1][1]["nombre"]
                    if name in data[mail][3]:
                        data[mail][3][name] += 1
                    else:
                        data[mail][3][name] = 1
                    with mutex:
                        with open(filepath, "r+") as file:
                            file.seek(0)
                            json.dump(data, file, indent = 4)
                            file.truncate()
                    print(f"[SERVIDOR]: Confirmación de envío '{data[mail][2][-1][1]['nombre']}' - Cliente {data[mail][1]}\n")
                    sock.sendall("Envío confirmado con éxito!\n".encode())
                    break
                else:
                    sock.sendall("Ingresa una respuesta válida.\n".encode())
            else:
                sock.sendall("Ingresa una respuesta válida.\n".encode())

def tramitarDevolucion(sock:socket.socket, filepath, mail):
     while True: 
        with mutex:
            with open(filepath, "r+") as file:
                data = json.load(file)
        hist = data[mail][2]
        today = datetime.today()
        transactions = []
        n = 1
        for i in range(len(hist)):
            actDate = dicttoDate(hist[i][1]["fecha"])
            if (today - actDate).days <= 365 and hist[i][1]["tipo"] == "compra" and hist[i][1]["recib"] == True and hist[i][1]["devo"] == False:
                transactions.append(hist[i])
                sock.sendall(f"[{n}] {hist[i][1]['nombre'].replace('_', ' ')} | {actDate.year}-{actDate.month}-{actDate.day}\n".encode())
                n += 1
        if transactions == []:
            sock.sendall("No hay transacciones que puedan ser reembolsadas.\n".encode())
            break
        else:
            sock.sendall("¿Cuál de los artículos siguientes deseas reembolsar? (0 = Salir)\n".encode())
            ans = sock.recv(1024).decode()
            if ans == "0":
                break
            elif ans.isnumeric() and 0 < int(ans) < n:
                ans = int(ans)
                sock.sendall(f"¿Deseas confirmar el reembolso de {transactions[ans - 1][1]['nombre'].replace('_', ' ')}? (1 = Aceptar - 0 = Cancelar)\n".encode())
                resp = sock.recv(1024).decode()
                if resp == "0":
                    sock.sendall("Acción cancelada.\n".encode())
                    break
                elif resp == "1":
                    name = transactions[ans - 1][1]["nombre"]
                    data[mail][2][transactions[ans - 1][0]][1]["devo"] = True
                    data[mail][2].append([len(data[mail][2]) + 1, accion("devo", f"{transactions[ans - 1][1]['nombre']} (Comprado el {dicttoDate(transactions[ans - 1][1]['fecha'])})").asdict()])
                    data[mail][3][name] -=1
                    with mutex:
                        with open(filepath, "r+") as file:
                            file.seek(0)
                            json.dump(data, file, indent = 4)  
                            file.truncate()
                    print(f"[SERVIDOR]: Reembolso '{data[mail][2][-1][1]['nombre']}' - Cliente {data[mail][1]}")
                    sock.sendall("Reembolso confirmado con éxito!\n".encode())
                    break
                else:
                    sock.sendall("Ingresa una respuesta válida.\n".encode())
            else:
                sock.sendall("Ingresa una respuesta válida.\n".encode())


def determinarAccion(sock:socket.socket, x, filepath1, filepath2, mail):
    while True:
        if x.isnumeric() and 0 < int(x) < 7:
            if x == "1":
                cambioContraseña(sock, filepath1, mail)
                break
            elif x == "2":
                catalogoCompra(sock, filepath2, filepath1, mail)
                break
            elif x == "3":
                verHistorial(sock, filepath1, mail)
                break
            elif x == "4":
                confirmarEnvio(sock, filepath1, mail)
                break
            elif x == "5":
                tramitarDevolucion(sock, filepath1, mail)
                break
        else:
            sock.sendall("Ingrese una acción válida.\n".encode())
            break

