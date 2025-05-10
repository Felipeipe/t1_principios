
# Importamos librerias
import socket
import threading
import json
import funcionesCliente
import funcionesEjecutivo

# Variables globales
path_clientes = "clientes.json"
path_articulos = "articulos.json"
path_ejecutivos = "ejecutivos.json"
path_inventario = "inventario_sinPublicar.json"

clientesEsperando= []
ejecutivosDisponibles = []
clientesConectados=[]
mutex = threading.Lock() # Este impone el mutex

def iniciar_chat(cliente, sockEjecutivo, path_articulos, path_inventario, path_clientes):
    global clientesEsperando, ejecutivosDisponibles, clientesConectados

    
    sockCliente = cliente[0]
    mailCliente = cliente[1]
    nombreCliente = cliente[2]
    connectEvent = cliente[3]
    endEvent = cliente[4]

    connectEvent.set()

    def escuchar_cliente():
        while not endEvent.is_set():
            try:
                mensaje = sockCliente.recv(1024).decode()
                if mensaje == ":disconnect:":
                    sockEjecutivo.send(f"{nombreCliente} ha salido del chat.\n".encode())
                    endEvent.set()
                    break
                sockEjecutivo.send(f"[{nombreCliente}] {mensaje}".encode())
            except Exception as e:
                print(f'[SERVER]: error cliente: {e}')
                endEvent.set()
                break

    def escuchar_ejecutivo():
        while not endEvent.is_set():
            try:
                mensaje = sockEjecutivo.recv(1024).decode()
                if mensaje == ":disconnect:":
                    sockCliente.send("Ejecutivo ha salido del chat.\n".encode())
                    endEvent.set()
                    break
                funcionesEjecutivo.command_parser(
                    sockEjecutivo, mensaje, path_articulos, path_inventario,
                    ejecutivosDisponibles, clientesConectados, clientesEsperando,
                    path_clientes, sockCliente, mailCliente, True
                )
            except Exception as e:
                print(f'[SERVER]: error ejecutivo: {e}')
                endEvent.set()
                break

    threading.Thread(target=escuchar_cliente).start()
    threading.Thread(target=escuchar_ejecutivo).start()


    
# Funcion de cliente
def cliente(sock, addr):
    global clientesEsperando
    global ejecutivosDisponibles
    global clientesConectados
    try:
        
        sock.sendall("\nPara iniciar sesión, ingresa tu correo y contraseña\n".encode())
        while True:
            # Revisamos que usuarios disponibles tenemos
            with mutex:
                with open(path_clientes, "r") as file:
                    data = json.load(file)
                    clientes = list(data.keys())
            sock.sendall("Ingresa tu correo: ".encode())
            email = sock.recv(1024).decode()
            if email in clientes:
                sock.sendall("\nIngresa tu contraseña: ".encode())
                passw = sock.recv(1024).decode()
                if passw == data[email][0]:
                    sock.sendall(f"\nHola, {data[email][1]}! ¿En qué te podemos ayudar hoy? (Ingresa un número)".encode())
                    with mutex:
                        clientData = [sock, email, data[email][1]]
                        clientesConectados.append(clientData)

                    while True:
                        sock.sendall("[1] Cambiar contraseña\n[2] Ver el catálogo de productos\n[3] Ver el historial de compras\n[4] Confirmar envíos\n[5] Solicitar la devolución de un artículo\n[6] Chat con ejecutivo\n[7] Cerrar sesión".encode())
                        ans = sock.recv(1024).decode()
                        if ans == "6":
                            connectEvent = threading.Event()
                            endEvent = threading.Event()
                            dataChat = [sock, email, data[email][1], connectEvent, endEvent]
                            with mutex:
                                clientesEsperando.append(dataChat)
                            sock.sendall("Esperando a que se conecte un ejecutivo...\n".encode())
                            if connectEvent.wait(timeout = 60):
                                sock.sendall("Conexión establecida con un ejecutivo. Redirigiendo...\n".encode())
                                sock.sendall("Sesión iniciada! Recuerda mantener el respeto en todo momento.\n".encode())
                                sock.sendall("Si desea desconectarse por favor escriba :disconnect:".encode())
                                endEvent.wait()
                                with mutex:
                                    with open(path_clientes, "r+") as file:
                                        histData = json.load(file)
                                        histData[email][2].append([len(histData[email][2]) + 1, funcionesCliente.accion("exec").asdict()])
                                        file.seek(0)
                                        json.dump(histData, file, indent = 4)
                            else:
                                sock.sendall("No hay ningún ejecutivo disponible en estos momentos. Intenta nuevamente más tarde.\n".encode())

                            sock.sendall("¿Se te ofrece algo más?".encode())
                        elif ans == "7":
                            try:
                                sock.sendall("Nos vemos!".encode())
                                with mutex:
                                    clientesConectados.remove(clientData)
                                sock.close()
                            except Exception as e:
                                print(f"Error inesperado: {e}")
                            break
                        else:
                            funcionesCliente.determinarAccion(sock, ans, path_clientes, path_articulos, email)
                            sock.sendall("¿Se te ofrece algo más?\n".encode())
                    break
                else:
                    sock.sendall("Contraseña incorrecta, ingrese sus datos nuevamente.".encode())
            else:
                sock.sendall("Correo no reconocido, ingrese sus datos nuevamente".encode())
    except (ConnectionResetError, ConnectionAbortedError):
        try:
            with mutex:
                clientesConectados.remove(clientData)
            print("pucha")
        except (ValueError, UnboundLocalError):
            pass
        
        try:
            with mutex:
                clientesEsperando.remove(clientData)
        except (ValueError, UnboundLocalError):
            pass

        print(f"[SERVIDOR] Cliente {addr} se desconectó abruptamente.")
    except Exception as e:
        print(f"[SERVIDOR] Error inesperado con {addr}: {e}")
    finally:
        sock.close()
        print(f"[SERVIDOR] Conexión a {addr} terminada.")  

def ejecutivo(sock,addr):
    global ejecutivosDisponibles
    global clientesConectados
    global clientesEsperando

    try:
        sock.sendall("\nPara iniciar sesión, ingresa tu correo y contraseña\n".encode())
        while True:
            # Revisamos que usuarios disponibles tenemos
            with mutex:
                with open(path_ejecutivos, "r") as file:
                    data = json.load(file)
                    ejecutivos = list(data.keys())

            sock.sendall("Ingresa tu correo: ".encode())
            email = sock.recv(1024).decode()
            if email in ejecutivos:
                sock.sendall("\nIngresa tu contraseña: ".encode())
                passw = sock.recv(1024).decode()
                if passw == data[email][0]:
                    with mutex:
                        ejecutivosDisponibles.append(sock)
                    
                    sock.sendall(f"Hola, {data[email][1]}! Actualmente, hay {len(clientesConectados)} cliente(s) en línea.\n".encode())
                    if len(clientesEsperando) != 0:
                        sock.sendall(f"Hay {len(clientesEsperando)} cliente(s) solicitando asistencia. Si desea establecer una conexión con alguno, escriba el comando :connect:\n".encode())
                    else:
                        sock.sendall("Para comenzar, ingresa un comando.\n".encode())
                    while True:
                        sock.sendall("Escribe :exit: para salir\n".encode())
                        ans = sock.recv(1024).decode()
                        if ans == ":exit:":
                            sock.sendall("Nos vemos!".encode())
                            with mutex:
                                ejecutivosDisponibles.remove(sock)
                            sock.close()
                            break
                        elif ans == ":connect:":
                            if len(clientesEsperando) == 0:
                                sock.sendall("No hay clientes esperando en estos momentos.\n".encode())
                            else:
                                with mutex:
                                    cliente = clientesEsperando.pop(0)
                                iniciar_chat(cliente, sock, path_articulos, path_inventario, path_clientes)
                                sock.sendall("Conexión con cliente exitosa, puede comenzar a chatear\n".encode())
                                
                                cliente[4].wait()
                        else:
                            funcionesEjecutivo.command_parser(sock, ans, path_articulos, path_inventario, ejecutivosDisponibles, clientesConectados, clientesEsperando, path_clientes)
                    break
                else:
                    sock.sendall("Contraseña incorrecta, ingrese sus datos nuevamente.\n".encode())
            else:
                sock.sendall("Correo no reconocido, ingrese sus datos nuevamente.\n".encode())
    except (ConnectionResetError, ConnectionAbortedError):
        try: 
            ejecutivosDisponibles.remove(sock)
        except ValueError:
            pass

        print(f"[SERVIDOR] Ejecutivo {addr} se desconectó abruptamente.")
    except Exception as e:
        print(f"[SERVIDOR] Error inesperado con {addr}: {e}")
    finally:
        sock.close()
        print(f"[SERVIDOR] Conexión a {addr} terminada.")  



if __name__ == "__main__":
    # Se configura el servidor para que corra localmente y en el puerto 8889.
    ip = '127.0.0.1'
    puerto = 8889

    # Se crea el socket y se instancia en las variables anteriores.
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((ip, puerto))
    s.listen(20)

    print(f"Servidor inicializado con éxito en el puerto {puerto}.")
    # Se buscan clientes que quieran conectarse.
    
    while True:
    
        
        # Se acepta la conexion de un cliente
        conn, addr = s.accept()

        # Se recibe el tipo de usuario, para determinar colas de prioridad
        tipo_usuario = conn.recv(1024)
        conn.send("Bienvenid@ a la plataforma de atención al cliente de TCG5!".encode())
        

        # Se inicia el thread del cliente o ejecutivo
        if tipo_usuario == b"Cliente":
            with mutex:
                num_clientes = len(clientesConectados)
            if num_clientes < 7:
                client_thread = threading.Thread(target=cliente, args=(conn, addr))
                client_thread.start()
                print(f"ID Cliente conectado desde {addr}")
            else:
                conn.send("Lo siento! Se ha alcanzado el límite de clientes conectados. \nPor favor, intente más tarde\n".encode())

        elif tipo_usuario == b"Ejecutivo":
            with mutex:
                num_ejecutivos = len(ejecutivosDisponibles)
            if num_ejecutivos < 3:
                print(f"ID Ejecutivo conectado desde {addr}")
                ejecutivo_thread = threading.Thread(target=ejecutivo, args=(conn, addr))
                ejecutivo_thread.start()
            else:
                conn.send("Lo siento! Se ha alcanzado el límite de ejecutivos conectados. \nPor favor, intente más tarde\n".encode())

        else:
            print(tipo_usuario)
            break

