import socket
import json
import sys
import threading
from datetime import datetime

class compra:
    def __init__(self, name, date, price = 0,  payStatus = False, shipStatus = False, recv = False, dev = False):
        self.name = name
        self.date = date
        self.price = price
        self.payStatus = payStatus
        self.shipStatus = shipStatus
        self.recv = recv
        self.dev = dev

    def changePS(self):
        self.payStatus = not self.payStatus

    def changeSS(self):
        self.shipStatus = not self.shipStatus

    def changeRecv(self):
        self.recv = not self.recv

    def changeDev(self):
        self.dev = not self.dev

    def asdict(self):
        return {"nombre":self.name, "fecha":self.date, "precio":self.price, "pago":self.payStatus, "envio":self.shipStatus, "recib":self.recv, "dev":self.dev}

mutex = threading.Lock()

def cambioContraseña(sock, filepath, mail):
    while True:
        sock.sendall("Ingrese su contraseña actual: ".encode())
        act = sock.recv(1024).decode()
        with mutex:
            with open(filepath, "r+") as file:
                data = json.load(file)
                if act == data[mail][0]:
                    while True:
                        sock.sendall("Ingrese su nueva contraseña: ".encode())
                        new = sock.recv(1024).decode()
                        sock.sendall("Repita su nueva contraseña: ".encode())
                        newRep = sock.recv(1024).decode()
                        if new == newRep:
                            data[mail][0] = new
                            file.seek(0)
                            json.dump(data, file, indent = 4)
                            file.truncate()
                            file.close()
                            sock.sendall("Contraseña cambiada con éxito!".encode())
                            print(f"[SERVIDOR]: Cambio de clave - Cliente {data[mail][1]}")
                            break
                        else:
                            sock.sendall("Las contraseñas no coinciden, intente nuevamente.".encode())
                    break
                else:
                    sock.sendall("Contraseña incorrecta, intente nuevamente.".encode())
    return None

def catalogoCompra(sock, filepath1, filepath2, mail):
    while True:
        with mutex:
            with open(filepath1, "r") as file1:
                data1 = json.load(file1)
                for key, value in data1.items():
                    sock.sendall(f"[{key}] {value[0]} - ${value[1]}\n".encode())
                sock.sendall("¿Desea comprar algún elemento del catálogo? Ingrese un número (0 = Salir)".encode())
                ans = sock.recv(1024).decode()
                if ans == '0':
                    break
                elif ans.isnumeric() and 0 < int(ans) < len(data1) + 1:
                    sock.sendall(f"Confirme la compra de '{data1[ans][0].lower()}' por {data1[ans][1]} (1 = Confirmar - 0 = Cancelar)".encode())
                    conf = sock.recv(1024).decode()
                    if conf == "1":
                        if data1[ans][2] > 0:
                            with mutex:
                                with open(filepath2, "r+") as file2:
                                    data2 = json.load(file2)
                                    data2[mail][2].append([len(data2[mail][2]) + 1, compra(str(data1[ans][0]), datetime.now(), data1[ans][1], True, True).asdict()])
                                    file2.seek(0)
                                    json.dump(data2, file2, indent = 4)
                                    file2.truncate()
                                    file2.close()
                                    data1[ans][2] -= 1
                                    file1.seek(0)
                                    json.dump(data1, file1)
                                    file1.truncate()
                                    file1.close()
                                    sock.sendall("Compra realizada con éxito!".encode())
                                    print(f"[SERVIDOR] Cliente {data2[mail][1]} ha comprado {data1[ans][0]} por {data1[ans][1]}")
                                    break
                        else:
                            sock.sendall("No hay stock del artículo seleccionado. Lo sentimos :(".encode())
                    elif conf == "0":
                        sock.sendall("Compra cancelada.".encode())
                        sock.sendall("¿Se te ofrece algo más?")
                    else:
                        sock.sendall("Ingrese una respuesta válida.".encode())
                else:
                    sock.sendall("Ingrese un artículo válido.".encode())
    return None

def verHistorial(sock, filepath, mail):
    while True:
        with mutex:
            with open(filepath, "r") as file:
                data = json.load(file)
                hist = data[mail][2]
                today = datetime.today()
                n = 0
                for action in hist:
                    actDate = hist[action][1]["fecha"]
                    if today - actDate.date <= 365:
                        sock.sendall(f"[{hist[action][0]}] {actDate}".encode())
                        n += 1
                sock.sendall("¿Desea más información sobre alguna transacción? Ingrese un número (0 = Salir)".encode())
                ans = sock.recv(1024).decode()
                if ans == "0":
                    break
                elif ans.isnumeric() and 0 < int(ans) < n + 1:
                    sock.sendall("Datos adicionales:".encode())


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



