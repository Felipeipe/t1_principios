import socket
import json
import sys
import threading
from datetime import datetime

class transaccion:
    def __init__(self, type, name, date, price = 0, recv = False, dev = False):
        assert type == "compra" or type == "venta"
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
            return {"tipo":self.type, "nombre":self.name, "fecha":self.date, "precio":self.price, "recib":self.recv, "dev":self.dev}
        else:
            return {"tipo":self.type, "nombre":self.name, "fecha":self.date, "precio":self.price}

def datetoDict(date):
    return {"año":date.year, "mes":date.month, "dia":date.day, "hora":date.time().hour, "minuto":date.time().minute, "segundo":date.time().second}

def dicttoDate(dict):
    return datetime.datetime(dict["año"], dict["mes"], dict["dia"], dict["hora"], dict["minuto"], dict["segundo"])

def logic(bool):
    if bool:
        return 1
    else:
        return 0

mutex = threading.Lock() 

def cambioContraseña(sock, filepath, mail): # cambiar la contraseña actual de un usuario
    while True:
        sock.sendall("Ingrese su contraseña actual: ".encode())
        act = sock.recv(1024).decode()
        with mutex:
            with open(filepath, "r+") as file: # se abre el archivo asociado a los clientes
                data = json.load(file)
                if act == data[mail][0]: # si la contraseña ingresada coincide con la registrada...
                    while True:
                        sock.sendall("Ingrese su nueva contraseña: ".encode()) 
                        new = sock.recv(1024).decode() # se recibe la contraseña nueva
                        sock.sendall("Repita su nueva contraseña: ".encode())
                        newRep = sock.recv(1024).decode() # se recibe una confirmación de la contraseña nueva
                        if new == newRep: # si las contraseñas coinciden...
                            data[mail][0] = new # se setea la contraseña ingresada cómo la nueva contraseña
                            file.seek(0)
                            json.dump(data, file, indent = 4)
                            file.truncate()
                            file.close()
                            sock.sendall("Contraseña cambiada con éxito!".encode())
                            print(f"[SERVIDOR]: Cambio de clave - Cliente {data[mail][1]}")
                            break
                        else:
                            sock.sendall("Las contraseñas no coinciden, intente nuevamente.".encode()) # si la nueva contraseña y su confirmación no coincide
                    break
                else:
                    sock.sendall("Contraseña incorrecta, intente nuevamente.".encode()) # si la contraseña ingresada no coincide con la registrada en la base de datos
    return None

def catalogoCompra(sock, filepath1, filepath2, mail): # ver el catálogo de la tienda y permitir comprar artículos (se podría agregar comprar más de una unidad por acción)
    while True:
        with mutex:
            with open(filepath1, "r+") as file1: # se abre el archivo JSON con los artículos
                data1 = json.load(file1)
                for key, value in data1.items():
                    sock.sendall(f"[{key}] {value[0]} - ${value[1]}\n".encode()) # se muestran los elementos del catálogo
                sock.sendall("¿Desea comprar algún elemento del catálogo? Ingrese un número (0 = Salir)".encode())
                ans = sock.recv(1024).decode()
                if ans == '0': # salir del catálogo sin comprar nada
                    break
                elif ans.isnumeric() and 0 < int(ans) < len(data1) + 1: # si el artículo es válido...
                    sock.sendall(f"Confirme la compra de '{data1[ans][0].lower()}' por {data1[ans][1]} (1 = Confirmar - 0 = Cancelar)".encode())
                    conf = sock.recv(1024).decode()
                    if conf == "1": # si se confirma la compra...
                        if data1[ans][2] > 0: # si hay stock...                          
                            with open(filepath2, "r+") as file2: # se abre el archivo asociado a los clientes
                                data2 = json.load(file2)
                                data2[mail][2].append([len(data2[mail][2]) + 1, transaccion("compra", str(data1[ans][0]), datetoDict(datetime.today()), data1[ans][1]).asdict()]) # se guarda la compra en el historial del cliente
                                file2.seek(0)
                                json.dump(data2, file2, indent = 4)
                                file2.truncate()
                                file2.close()
                                data1[ans][2] -= 1 # se reduce el stock luego de la compra
                                file1.seek(0)
                                json.dump(data1, file1)
                                file1.truncate()
                                file1.close()
                                sock.sendall("Compra realizada con éxito!".encode())
                                print(f"[SERVIDOR] Cliente {data2[mail][1]} ha comprado {data1[ans][0]} por {data1[ans][1]}")
                                break
                        else:
                            sock.sendall("No hay stock del artículo seleccionado. Lo sentimos ".encode()) # no hay stock
                    elif conf == "0":
                        sock.sendall("Compra cancelada.".encode()) # no se confirma la compra del artículo
                        sock.sendall("¿Se te ofrece algo más?".encode())
                    else:
                        sock.sendall("Ingrese una respuesta válida.".encode()) # se ingresa una respuesta inválida al confirmar la compra
                else:
                    sock.sendall("Ingrese un artículo válido.".encode()) # se ingresa una id inválida al elegir un artículo
    return None

def verHistorial(sock, filepath, mail):
    while True:
        with mutex:
            with open(filepath, "r") as file:
                data = json.load(file)
                hist = data[mail][2]
                today = datetime.today()
                n = 1
                transactions = []
                for action in hist:
                    actDate = dicttoDate(hist[action][1]["fecha"])
                    if today - actDate.date <= 365:
                        transactions.append(hist[action][1])
                        sock.sendall(f"{n} {actDate.year}-{actDate.month}-{actDate.day}".encode())
                        n += 1
                sock.sendall("¿Desea más información sobre alguna transacción? Ingrese un número (0 = Salir)".encode())
                ans = sock.recv(1024).decode()
                if ans == "0":
                    sock.sendall("¿Se te ofrece algo más?".encode())
                    break
                elif ans.isnumeric() and 0 < int(ans) < n + 1: 
                    sock.sendall("Datos:".encode())
                    sock.sendall(f"Fecha - {transactions[ans - 1]["fecha"]}".encode())
                    sock.sendall(f"Precio - {transactions[ans - 1]["precio"]}".encode())
                    sock.sendall(f"Nombre de artículo - {transactions[ans - 1]["nombre"]}".encode())
                    if transactions[ans - 1]["tipo"] == "compra":
                        sock.sendall(f"El artículo ha sido pagado{logic(not transactions[ans - 1]["recib"])*" y está en camino."}{logic(transactions[ans - 1]["recib"])*", su envío fue confirmado"} {logic(transactions[ans - 1]["dev"])*", y se ha tramitado su devolución."}")
                    sock.sendall("¿Se te ofrece algo más?".encode())
                    break
                else:
                    sock.sendall("Ingresa una respuesta válida.".encode())

def confEnv(sock, filepath, mail):
    while True: 
        with mutex:
            with open(filepath, "r+") as file:
                data = json.load(file)
                hist = data[mail][2]
                today = datetime.today()
                sock.sendall("¿Cuál de los siguientes artículos recibió? (0 = Salir)".encode())
                n = 1
                transactions = []
                for action in hist:
                    actDate = dicttoDate(hist[action][1]["fecha"])
                    if today - actDate <= 365 and hist[action][1]["tipo"] == "compra" and hist[action][1]["recib"] == False:
                        transactions.append(hist[action][1])
                        sock.sendall(f"[{n}] {hist[action][1]["nombre"]} | {actDate.year}-{actDate.month}-{actDate.day}".encode())
                        n += 1
                ans = sock.recv(1024).decode()
                if ans  == "0":
                    sock.sendall("¿Se te ofrece algo más?")
                    break
                elif 

def determinarAccion(sock, x, filepath1, filepath2, mail):
    while True:
        if x.isnumeric() and 0 < int(x) < 4:
            if x == "1":
                cambioContraseña(sock, filepath1, mail)
                break
            elif x == "2":
                catalogoCompra(sock, filepath2, filepath1, mail)
                break
            elif x == "3":
                verHistorial(sock, filepath1, mail)
                break
        else:
            sock.sendall("Ingrese una acción válida.".encode())


