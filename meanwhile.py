def intentarEmpate(clientesEsperando,ejecutivosDisponibles):
    with mutex:
        if clientesEsperando and ejecutivosDisponibles:
            cliente_sock = clientesEsperando.pop(0)
            ejecutivo_sock = ejecutivosDisponibles.pop(0)
            chat_thread = threading.Thread(target=canalChat, args=(cliente_sock, ejecutivo_sock,"ejecutivo", "cliente"))
            chat_thread.start()
    
def comenzarChat(sock, clientesEsperando, ejecutivosDisponibles):
    if ejecutivosDisponibles:
        clientesEsperando.append(sock)
        intentarEmpate(clientesEsperando,ejecutivosDisponibles)
    else:
        sock.sendall("No hay ningún ejecutivo conectado en este momento. Por favor, intente más tarde".encode())


#####

def ejecutivo(sock,addr):
    global ejecutivosDisponibles
    global clientesConectados
    global clientesEsperando

    try:
        sock.sendall("Para iniciar sesión, ingresa tu correo y contraseña".encode())
        while True:
            # Revisamos que usuarios disponibles tenemos
            with mutex:
                with open(path_ejecutivos, "r") as file:
                    data = json.load(file)
                    ejecutivos = list(data.keys())
                    file.close()
            sock.sendall("Ingresa tu correo: ".encode())
            email = sock.recv(1024).decode()
            if email in ejecutivos:
                sock.sendall("Ingresa tu contraseña: ".encode())
                passw = sock.recv(1024).decode()
                if passw == data[email][0]:
                    sock.sendall(f"Hola, {data[email][1]}! Actualmente, hay {len(clientesConectados)} clientes en línea".encode())
                    with mutex:
                        ejecutivosDisponibles.append(sock)
                    funcionesCliente.intentarEmpate(clientesEsperando, ejecutivosDisponibles)
                    while True:
                        sock.sendall("Escriba 0 para salir".encode())
                        ans = sock.recv(1024).decode()
                        if ans == "0":
                            sock.sendall("Nos vemos!".encode())
                            ejecutivosDisponibles.remove(sock)
                            sock.close()
                            break
                        else:
                            sock.sendall("¿Se te ofrece algo más?\n".encode())
                    break
                else:
                    sock.sendall("Contraseña incorrecta, ingrese sus datos nuevamente.".encode())
            else:
                sock.sendall("Correo no reconocido, ingrese sus datos nuevamente".encode())
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