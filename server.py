
# Importamos librerias
import socket
import threading
import json
import funcionesCliente

# Variables globales
directorio_1 = "clientes.json"
directorio_2 = "articulos.json"
directorio_3 = "ejecutivos.json"
clientesEsperando= []
ejecutivosDisponibles = []
mutex = threading.Lock() # Este impone el mutex

# Funcion de cliente
def cliente(sock, addr):
    try:
        global clientesEsperando
        sock.sendall("Para iniciar sesión, ingresa tu correo y contraseña".encode())
        while True:
            # Revisamos que usuarios disponibles tenemos
            with mutex:
                with open(directorio_1, "r") as file:
                    data = json.load(file)
                    clientes = list(data.keys())
                    file.close()
            sock.sendall("Ingresa tu correo: ".encode())
            email = sock.recv(1024).decode()
            if email in clientes:
                sock.sendall("Ingresa tu contraseña: ".encode())
                passw = sock.recv(1024).decode()
                if passw == data[email][0]:
                    sock.sendall(f"Hola, {data[email][1]}! ¿En qué te podemos ayudar hoy? (Ingresa un número)".encode())
                    while True:
                        sock.sendall("[1] Cambiar contraseña\n[2] Ver el catálogo de productos\n[3] Ver el historial de compras\n[4] Confirmar envíos\n[5] Solicitar la devolución de un artículo\n[6] Cerrar sesión".encode())
                        ans = sock.recv(1024).decode()
                        if ans == "6":
                            sock.sendall("Nos vemos!".encode())
                            sock.close()
                            break
                        else:
                            funcionesCliente.determinarAccion(sock, ans, directorio_1, directorio_2, email)
                            sock.sendall("¿Se te ofrece algo más?\n".encode())
                    break
                else:
                    sock.sendall("Contraseña incorrecta, ingrese sus datos nuevamente.".encode())
            else:
                sock.sendall("Correo no reconocido, ingrese sus datos nuevamente".encode())
    except (ConnectionResetError, ConnectionAbortedError):
        print(f"[SERVIDOR] Cliente {addr} se desconectó abruptamente.")
    except Exception as e:
        print(f"[SERVIDOR] Error inesperado con {addr}: {e}")
    finally:
        sock.close()
        print(f"[SERVIDOR] Conexión a {addr} terminada.")  

def ejecutivo(sock):
    pass

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
            print(f"Cliente conectado desde {addr}")
            client_thread = threading.Thread(target=cliente, args=(conn, addr))
            client_thread.start()
        elif tipo_usuario == b"Ejecutivo":
            print(f"Ejecutivo conectado desde {addr}")
            ejecutivo_thread = threading.Thread(target=ejecutivo, args=(conn, addr))
            ejecutivo_thread.start()
        else:
            print(tipo_usuario)
            break