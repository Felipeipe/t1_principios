"""
Servidor cookie clicker
"""

# Importamos librerias
import socket
import threading
import json

# Variables globales
FILEPATH_1 = "clientes.json"
FILEPATH_2 = "ejecutivos.json"
CLIENTS_LIST = []
EJECUTIVOS_LIST = []
mutex = threading.Lock() # Este impone el mutex


# Funcion de cliente
def cliente(sock):
    global CLIENTS_LIST, FILEPATH_1
    while True:
        # Revisamos que usuarios disponibles tenemos
        with mutex:
            with open(FILEPATH_1, "r") as file:
                data = json.load(file)
                clientes = list(data.keys())
                print(clientes)
                file.close()

        # Revisamos el mensaje recibido
        cliente = sock.recv(1024).decode()
        if cliente in clientes: # Si esta en la lista de clientes
            sock.send('Asistente: Yo a ti te conozco...'.encode())
            sock.send('¿A quien le sumas 1 galleta? \n Escribe ::exit para salir'.encode())
            print(f'Cliente {nombre} se ha conectado.')

            while True:
                try:
                    data = sock.recv(1024).decode()
                except:
                    break

                if data == "::exit":
                    sock.send("Chao cuidate!".encode())
                    
                    # Se modifican las variables globales usando un mutex.
                    with mutex:
                        CLIENTS_LIST.remove(sock)
                    sock.close()
                    print(f'Cliente {nombre} se ha desconectado.')
                    break

                elif data in names:
                    #muestra los pedidos de los clientes
                    print(f'El cliente {nombre} le da una galleta a {data}')
                    with mutex:
                        with open(FILEPATH) as file:
                            database = json.load(file)
                            database[data] +=1
                            amount = database[data]
                            file.close()
                        with open(FILEPATH, "w") as file:
                            json.dump(database, file)
                            file.close()
                        
                    sock.send(f'Gracias a ti, {data} ahora tiene {amount} galleta(s)'.encode())
                    
                else:
                    sock.send('No conozco esa persona :c, intenta con otro nombre'.encode())
            return None

        elif nombre == '::exit':
            with mutex:
                CLIENTS_LIST.remove(sock)
            sock.close()
            return None

        else: 
            sock.send('No te conozco y no hablo con desconocidos :C \nVuelve a intentarlo o ::exit para salir.'.encode())

def ejecutivo(sock):
    pass

if __name__ == "__main__":
    # Se configura el servidor para que corra localmente y en el puerto 8889.
    HOST = '127.0.0.1'
    PORT = 8889

    # Se crea el socket y se instancia en las variables anteriores.
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((HOST, PORT))
    s.listen(20)

    print(f"Servidor inicializado con éxito en el puerto {PORT}.")

    # Se buscan clientes que quieran conectarse.
    while True:

        # Se acepta la conexion de un cliente
        conn, addr = s.accept()

        # Se manda el mensaje de bienvenida
        tipo_usuario = conn.recv(1024)
        conn.send("Bienvenid@ a mi clicker :D \n Te conozco? (dime tu nombre)".encode())
        

        # Se inicia el thread del cliente o ejecutivo
        if tipo_usuario == "Cliente":
            CLIENTS_LIST.append(conn)
            client_thread = threading.Thread(target=cliente, args=(conn,))
            client_thread.start()
        elif tipo_usuario == "Ejecutivo":
            EJECUTIVOS_LIST.append(conn)
            ejecutivo_thread = threading.Thread(target=ejecutivo, args=(conn,))
            ejecutivo_thread.start()
        else:
            print("Type Error")
            s.close()
            break