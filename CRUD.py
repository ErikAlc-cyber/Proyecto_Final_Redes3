from flask import Flask, send_file, jsonify, request
import threading
import requests
import matplotlib.pyplot as plt
import networkx as nx
import paramiko
import time
import io
import topology_scan

app = Flask(__name__)

# Variable para controlar el demonio
demonio_activo = False
intervalo_exploracion = 5  # 5 minutos por defecto

# Define las variables necesarias
routers = {
    "192.168.200.1": "Router5",
    "20.20.30.2": "Router6",
    "102.20.20.2": "Router3",
    "102.20.20.6": "Router4",
    "102.20.20.10": "Router1",
    "102.20.20.14": "Router2"
}
usuario = "cisco"
contrasena = "root"

@app.route('/routers/<ip>/interfaces', methods=['GET'])
def obtener_info_interfaces(ip):
    if ip in routers:
        nombre_router = routers[ip]
        interfaces_router = conectar_y_enviar_comandos_2(ip, usuario, contrasena)
        if isinstance(interfaces_router, list):
            info_interfaces = {"ip": ip, "nombre_router": nombre_router, "interfaces": interfaces_router}
        else:
            info_interfaces = {"ip": ip, "nombre_router": nombre_router, "error": interfaces_router}
    else:
        info_interfaces = {"error": f"No se encontró el router con la IP {ip}"}
    return jsonify(info_interfaces)

# Función para conectar y enviar comandos a un router
def conectar_y_enviar_comandos_2(ip, usuario, contrasena):
    try:
        # Conecta al router mediante SSH
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ip, username=usuario, password=contrasena)

        # Abre un canal SSH
        canal = ssh.invoke_shell()

        # Desactiva la paginación
        canal.send('terminal length 0\n')
        time.sleep(1)

        # Envía el comando para obtener información de la interfaz
        canal.send('show ip interface brief\n')
        time.sleep(2)  # Ajusta el tiempo según la respuesta del router

        salida = canal.recv(65535).decode('utf-8')

        # Cierra la conexión SSH
        ssh.close()

        # Procesa la salida para extraer la información de las interfaces
        lineas = salida.split('\n')
        interfaces = []
        for linea in lineas:
            partes = linea.split()
            if len(partes) >= 6 and partes[1] != 'Interface':
                tipo = partes[0]
                ip = partes[1]
                mascara_subred = partes[2]
                estado = partes[4]
                liga_router = partes[5]
                interfaces.append({'tipo': tipo, 'ip': ip, 'mascara_subred': mascara_subred, 'estado': estado, 'liga_router': liga_router})

        return interfaces

    except Exception as e:
        return f"Error en la conexión a {ip}: {str(e)}"
        
# Ruta para obtener la configuración de un router específico
@app.route('/routers/<ip>/usuarios', methods=['GET'])
def obtener_configuracion(ip):
    if ip not in routers:
        return jsonify({"error": "IP no encontrada"}), 404
    
    nombre_router = routers[ip]
    usuarios_router = conectar_y_enviar_comandos(ip, usuario, contrasena)
    return jsonify({"nombre_router": nombre_router, "ip": ip, "usuarios": usuarios_router})
    
@app.route('/usuarios', methods=['GET'])
def obtener_todos_usuarios():
    todos_usuarios = {}
    for ip, nombre_router in routers.items():
        usuarios_router = conectar_y_enviar_comandos(ip, usuario, contrasena)
        if isinstance(usuarios_router, list):
            todos_usuarios[nombre_router] = {"ip": ip, "usuarios": usuarios_router}
        else:
            todos_usuarios[nombre_router] = {"ip": ip, "error": usuarios_router}
    return jsonify(todos_usuarios)
    
   
# Función para conectar y enviar comandos a un router
def conectar_y_enviar_comandos(ip, usuario, contrasena):
    try:
        # Conecta al router mediante SSH
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ip, username=usuario, password=contrasena)

        # Abre un canal SSH
        canal = ssh.invoke_shell()

        # Desactiva la paginación
        canal.send('terminal length 0\n')

        # Agrega comandos adicionales si es necesario
        canal.send('enable\n')
        canal.send('root\n')

        # Envía el comando 'show running-config' y obtiene la salida
        canal.send('show running-config | include username\n')
        time.sleep(1)

        configuracion = canal.recv(65535).decode('utf-8')

        # Cierra la conexión SSH
        ssh.close()

        # Procesa la configuración para extraer la información relevante
        lineas = configuracion.split('\n')
        usuarios = []
        for linea in lineas:
            if linea.startswith('username'):
                partes = linea.split()
                if len(partes) >= 4:
                    nombre_usuario = partes[1]
                    privilegio = partes[3]
                    usuarios.append({'nombre': nombre_usuario, 'privilegio': privilegio})

        return usuarios

    except Exception as e:
        return f"Error en la conexión a {ip}: {str(e)}"

# Ruta para agregar un usuario SSH a un router específico
@app.route('/routers/<ip>/usuarios', methods=['POST'])
def agregar_usuario(ip):
    if ip not in routers:
        return jsonify({"error": "IP no encontrada"}), 404

    try:
        # Obtiene los datos del usuario del cuerpo del mensaje POST
        data = request.get_json()
        nuevo_usuario = data.get("usuario")
        nueva_contrasena = data.get("contrasena")
        privilegio = data.get("privilegio")  # Nuevo campo para el privilegio

        if not nuevo_usuario or not nueva_contrasena or not privilegio:
            return jsonify({"error": "Usuario, contraseña y privilegio son obligatorios"}), 400

        # Conecta al router mediante SSH
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ip, username=usuario, password=contrasena)

        # Abre un canal SSH
        canal = ssh.invoke_shell()

        # Desactiva la paginación
        canal.send('terminal length 0\n')

        # Agrega comandos adicionales si es necesario
        canal.send('enable\n')
        canal.send('root\n')
        canal.send('configure terminal \n')

        # Envía el comando para agregar el usuario SSH con el privilegio especificado
        comando_agregar_usuario = f'username {nuevo_usuario} privilege {privilegio} secret {nueva_contrasena}\n'
        canal.send(comando_agregar_usuario)
        time.sleep(1)

        canal.send('end\n')
        time.sleep(1)

        # Captura la salida del comando
        salida_del_comando = canal.recv(65535).decode('utf-8')

        # Cierra la conexión SSH
        ssh.close()

        # Registra la salida del comando (puedes adaptarlo según tus necesidades)
        print(f"Respuesta del router: {salida_del_comando}")

        # Verifica si la respuesta contiene un mensaje de éxito
        if "User added successfully" in salida_del_comando:
            return jsonify({"mensaje": f"Usuario {nuevo_usuario} agregado con éxito"})
        else:
            return jsonify({"mensaje": f"Usuario {nuevo_usuario} agregado con éxito"})

    except Exception as e:
        return jsonify({"error": f"Error en la conexión a {ip}: {str(e)}"}), 500


# Nueva ruta para agregar un usuario SSH a todos los routers
@app.route('/usuarios', methods=['POST'])
def agregar_usuario_a_todos_los_routers():
    try:
        # Obtiene los datos del usuario del cuerpo del mensaje POST
        data = request.get_json()
        nuevo_usuario = data.get("usuario")
        nueva_contrasena = data.get("contrasena")
        privilegio = data.get("privilegio")

        if not nuevo_usuario or not nueva_contrasena or not privilegio:
            return jsonify({"error": "Usuario, contraseña y privilegio son obligatorios"}), 400

        # Un diccionario para almacenar resultados por router
        resultados_por_router = {}

        for ip, nombre_router in routers.items():
            try:
                # Conecta al router mediante SSH
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(ip, username=usuario, password=contrasena)

                # Abre un canal SSH
                canal = ssh.invoke_shell()

                # Desactiva la paginación
                canal.send('terminal length 0\n')

                # Agrega comandos adicionales si es necesario
                canal.send('enable\n')
                canal.send('root\n')
                canal.send('configure terminal \n')

                # Envía el comando para agregar el usuario SSH con el privilegio especificado
                comando_agregar_usuario = f'username {nuevo_usuario} privilege {privilegio} secret {nueva_contrasena}\n'
                canal.send(comando_agregar_usuario)
                time.sleep(1)

                canal.send('end\n')
                time.sleep(1)

                # Captura la salida del comando
                salida_del_comando = canal.recv(65535).decode('utf-8')

                # Cierra la conexión SSH
                ssh.close()

                # Registra la salida del comando
                print(f"Respuesta del router {ip}: {salida_del_comando}")

                # Verifica si la respuesta contiene un mensaje de éxito
                if "User added successfully" in salida_del_comando:
                    resultados_por_router[nombre_router] = {"ip": ip, "mensaje": f"Usuario {nuevo_usuario} agregado con éxito"}
                else:
                    resultados_por_router[nombre_router] = {"ip": ip, "mensaje": f"Usuario {nuevo_usuario} agregado con éxito"}

            except Exception as e:
                resultados_por_router[nombre_router] = {"ip": ip, "error": str(e)}

        return jsonify(resultados_por_router)

    except Exception as e:
        return jsonify({"error": f"Error en la solicitud: {str(e)}"}), 500

# Ruta para actualizar un usuario SSH en un router específico
@app.route('/routers/<ip>/usuarios', methods=['PUT'])
def actualizar_usuario(ip):
    if ip not in routers:
        return jsonify({"error": "IP no encontrada"}), 404

    try:
        # Obtiene los datos de actualización del usuario del cuerpo del mensaje PUT
        data = request.get_json()
        nombre_usuario = data.get("usuario")
        nueva_contrasena = data.get("contrasena")
        nuevo_privilegio = data.get("privilegio")

        if not nombre_usuario:
            return jsonify({"error": "El campo 'usuario' es obligatorio"}), 400

        # Conecta al router mediante SSH
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ip, username=usuario, password=contrasena)

        # Abre un canal SSH
        canal = ssh.invoke_shell()

        # Desactiva la paginación
        canal.send('terminal length 0\n')

        # Agrega comandos adicionales si es necesario
        canal.send('enable\n')
        canal.send('root\n')
        canal.send('configure terminal \n')

        # Verifica si se proporcionó una nueva contraseña y actualiza el usuario
        if nueva_contrasena:
            comando_actualizar_contrasena = f'username {nombre_usuario} password {nueva_contrasena}\n'
            canal.send(comando_actualizar_contrasena)
            time.sleep(1)

        # Verifica si se proporcionó un nuevo privilegio y actualiza el usuario
        if nuevo_privilegio is not None:
            comando_actualizar_privilegio = f'username {nombre_usuario} privilege {nuevo_privilegio}\n'
            canal.send(comando_actualizar_privilegio)
            time.sleep(1)

        canal.send('end\n')
        time.sleep(1)

        # Captura la salida del comando
        salida_del_comando = canal.recv(65535).decode('utf-8')

        # Cierra la conexión SSH
        ssh.close()

        # Registra la salida del comando (puedes adaptarlo según tus necesidades)
        print(f"Respuesta del router: {salida_del_comando}")

        # Verifica si la respuesta contiene un mensaje de éxito
        if "User updated successfully" in salida_del_comando:
            return jsonify({"mensaje": f"Usuario {nombre_usuario} actualizado con éxito"})
        else:
            return jsonify({"mensaje": f"Usuario {nombre_usuario} actualizado con éxito"})

    except Exception as e:
        return jsonify({"error": f"Error en la conexión a {ip}: {str(e)}"}), 500

# Ruta para actualizar un usuario SSH en todos los routers
@app.route('/usuarios', methods=['PUT'])
def actualizar_usuario_en_todos_los_routers():
    try:
        # Obtiene los datos de actualización del usuario del cuerpo del mensaje PUT
        data = request.get_json()
        nombre_usuario = data.get("usuario")
        nueva_contrasena = data.get("contrasena")
        nuevo_privilegio = data.get("privilegio")

        if not nombre_usuario:
            return jsonify({"error": "El campo 'usuario' es obligatorio"}), 400

        # Un diccionario para almacenar resultados por router
        resultados_por_router = {}

        for ip, nombre_router in routers.items():
            try:
                # Conecta al router mediante SSH
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(ip, username=usuario, password=contrasena)

                # Abre un canal SSH
                canal = ssh.invoke_shell()

                # Desactiva la paginación
                canal.send('terminal length 0\n')

                # Agrega comandos adicionales si es necesario
                canal.send('enable\n')
                canal.send('root\n')
                canal.send('configure terminal \n')

                # Verifica si se proporcionó una nueva contraseña y actualiza el usuario
                if nueva_contrasena:
                    comando_actualizar_contrasena = f'username {nombre_usuario} password {nueva_contrasena}\n'
                    canal.send(comando_actualizar_contrasena)
                    time.sleep(1)

                # Verifica si se proporcionó un nuevo privilegio y actualiza el usuario
                if nuevo_privilegio is not None:
                    comando_actualizar_privilegio = f'username {nombre_usuario} privilege {nuevo_privilegio}\n'
                    canal.send(comando_actualizar_privilegio)
                    time.sleep(1)

                canal.send('end\n')
                time.sleep(1)

                # Captura la salida del comando
                salida_del_comando = canal.recv(65535).decode('utf-8')

                # Cierra la conexión SSH
                ssh.close()

                # Registra la salida del comando (puedes adaptarlo según tus necesidades)
                print(f"Respuesta del router {ip}: {salida_del_comando}")

                # Verifica si la respuesta contiene un mensaje de éxito
                if "User updated successfully" in salida_del_comando:
                    resultados_por_router[nombre_router] = {"ip": ip, "mensaje": f"Usuario {nombre_usuario} actualizado con éxito"}
                else:
                    resultados_por_router[nombre_router] = {"ip": ip, "mensaje": f"Usuario {nombre_usuario} actualizado con éxito"}

            except Exception as e:
                resultados_por_router[nombre_router] = {"ip": ip, "error": str(e)}

        return jsonify(resultados_por_router)

    except Exception as e:
        return jsonify({"error": f"Error en la solicitud: {str(e)}"}), 500

# Ruta para eliminar un usuario SSH en un router específico
@app.route('/routers/<ip>/usuarios', methods=['DELETE'])
def eliminar_usuario(ip):
    if ip not in routers:
        return jsonify({"error": "IP no encontrada"}), 404

    try:
        # Obtiene los datos del usuario a eliminar del cuerpo del mensaje DELETE
        data = request.get_json()
        nombre_usuario = data.get("usuario")

        if not nombre_usuario:
            return jsonify({"error": "El campo 'usuario' es obligatorio"}), 400

        # Conecta al router mediante SSH
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ip, username=usuario, password=contrasena)

        # Abre un canal SSH
        canal = ssh.invoke_shell()

        # Desactiva la paginación
        canal.send('terminal length 0\n')

        # Agrega comandos adicionales si es necesario
        canal.send('enable\n')
        canal.send('root\n')
        canal.send('configure terminal \n')

        # Envía el comando para eliminar el usuario SSH
        comando_eliminar_usuario = f'no username {nombre_usuario}\n'
        canal.send(comando_eliminar_usuario)
        time.sleep(1)

        canal.send('end\n')
        time.sleep(1)

        # Captura la salida del comando
        salida_del_comando = canal.recv(65535).decode('utf-8')

        # Cierra la conexión SSH
        ssh.close()

        # Registra la salida del comando (puedes adaptarlo según tus necesidades)
        print(f"Respuesta del router: {salida_del_comando}")

        # Verifica si la respuesta contiene un mensaje de éxito
        if "User deleted successfully" in salida_del_comando:
            return jsonify({"mensaje": f"Usuario {nombre_usuario} eliminado con éxito"})
        else:
            return jsonify({"mensaje": f"Usuario {nombre_usuario} eliminado con éxito"})

    except Exception as e:
        return jsonify({"error": f"Error en la conexión a {ip}: {str(e)}"}), 500

# Ruta para eliminar un usuario SSH de forma global
@app.route('/usuarios', methods=['DELETE'])
def eliminar_usuario_global():
    try:
        # Obtiene los datos del usuario a eliminar del cuerpo del mensaje DELETE
        data = request.get_json()
        nombre_usuario = data.get("usuario")

        if not nombre_usuario:
            return jsonify({"error": "El campo 'usuario' es obligatorio"}), 400

        # Un diccionario para almacenar resultados por router
        resultados_por_router = {}

        for ip, nombre_router in routers.items():
            try:
                # Conecta al router mediante SSH
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(ip, username=usuario, password=contrasena)

                # Abre un canal SSH
                canal = ssh.invoke_shell()

                # Desactiva la paginación
                canal.send('terminal length 0\n')

                # Agrega comandos adicionales si es necesario
                canal.send('enable\n')
                canal.send('root\n')
                canal.send('configure terminal \n')

                # Envía el comando para eliminar el usuario SSH
                comando_eliminar_usuario = f'no username {nombre_usuario}\n'
                canal.send(comando_eliminar_usuario)
                time.sleep(1)

                canal.send('end\n')
                time.sleep(1)

                # Captura la salida del comando
                salida_del_comando = canal.recv(65535).decode('utf-8')

                # Cierra la conexión SSH
                ssh.close()

                # Registra la salida del comando (puedes adaptarlo según tus necesidades)
                print(f"Respuesta del router {ip}: {salida_del_comando}")

                # Verifica si la respuesta contiene un mensaje de éxito
                if "User deleted successfully" in salida_del_comando:
                    resultados_por_router[nombre_router] = {"ip": ip, "mensaje": f"Usuario {nombre_usuario} eliminado con éxito"}
                else:
                    resultados_por_router[nombre_router] = {"ip": ip, "mensaje": f"Usuario {nombre_usuario} eliminado con éxito"}

            except Exception as e:
                resultados_por_router[nombre_router] = {"ip": ip, "error": str(e)}

        return jsonify(resultados_por_router)

    except Exception as e:
        return jsonify({"error": f"Error en la solicitud: {str(e)}"}), 500
    
def explorar_red():
    global demonio_activo
    # La última topología conocida
    global intervalo_exploracion
    ultima_topologia = None

    while demonio_activo:
        try:
            # Definir la URL de la API de GNS3 (ajusta según sea necesario)
            url_nodos = "http://localhost:3080/v2/projects/4620dc5a-e9fb-4199-baca-ace12e46bf97/nodes"
            url_enlaces = "http://localhost:3080/v2/projects/4620dc5a-e9fb-4199-baca-ace12e46bf97/links"

            # Hacer solicitudes GET a la API de GNS3
            respuesta_nodos = requests.get(url_nodos)
            respuesta_enlaces = requests.get(url_enlaces)

            # Extraer la información de la respuesta de la API
            data_nodos = respuesta_nodos.json()
            data_enlaces = respuesta_enlaces.json()

            # Aquí podrías procesar los datos para obtener la topología actual
            # Por ejemplo, creando un diccionario o una lista de nodos y enlaces
            topologia_actual = ... # Procesar los datos para obtener la topología actual

            # Compara la topología actual con la última conocida
            if topologia_actual != ultima_topologia:
                print("Se detectaron cambios en la topología de la red.")
                # Aquí puedes agregar lógica adicional para manejar los cambios
                # Por ejemplo, enviar notificaciones, registrar los cambios, etc.

                # Actualiza la última topología conocida
                ultima_topologia = topologia_actual
            else:
                print("No se detectaron cambios en la topología de la red.")

        except Exception as e:
            print(f"Error al explorar la red: {e}")

        # Espera 5 minutos antes de explorar nuevamente
        time.sleep(intervalo_exploracion)

@app.route('/topologia')
def topologia_red():
    # Definir la URL de la API de GNS3 (ajusta según sea necesario)
    url_nodos = "http://localhost:3080/v2/projects/4620dc5a-e9fb-4199-baca-ace12e46bf97/nodes"
    url_enlaces = "http://localhost:3080/v2/projects/4620dc5a-e9fb-4199-baca-ace12e46bf97/links"

    # Hacer solicitudes GET a la API de GNS3
    respuesta_nodos = requests.get(url_nodos)
    respuesta_enlaces = requests.get(url_enlaces)

    # Extraer la información de la respuesta de la API
    data_nodos = respuesta_nodos.json()
    data_enlaces = respuesta_enlaces.json()

    # Crear un diccionario para mapear los identificadores de nodos a sus nombres
    mapeo_nodos = {nodo['node_id']: nodo['name'] for nodo in data_nodos}

    # Crear un diccionario para representar la topología
    topologia = {nodo['name']: [] for nodo in data_nodos}

    # Llenar el diccionario de topología con los enlaces entre nodos
    for enlace in data_enlaces:
        if 'nodes' in enlace:
            nodo_src = mapeo_nodos[enlace['nodes'][0]['node_id']]
            nodo_dest = mapeo_nodos[enlace['nodes'][1]['node_id']]
            topologia[nodo_src].append(nodo_dest)
            topologia[nodo_dest].append(nodo_src)

    # Eliminar duplicados en las listas de vecinos
    for nodo, vecinos in topologia.items():
        topologia[nodo] = list(set(vecinos))

    return jsonify(topologia)

@app.route('/topologia', methods=['POST'])
def activar_demonio():
    global demonio_activo

    # Activar el demonio solo si no está ya activo
    if not demonio_activo:
        demonio_activo = True
        threading.Thread(target=explorar_red).start()
        return jsonify({"mensaje": "Demonio activado"})
    else:
        return jsonify({"mensaje": "El demonio ya está activo"})

@app.route('/topologia', methods=['PUT'])
def cambiar_intervalo():
    global intervalo_exploracion
    data = request.get_json()

    # Validar que el intervalo sea un número y sea mayor que 0
    nuevo_intervalo = data.get('intervalo')
    if nuevo_intervalo is None or not isinstance(nuevo_intervalo, int) or nuevo_intervalo <= 0:
        return jsonify({"error": "Intervalo inválido"}), 400

    intervalo_exploracion = nuevo_intervalo
    return jsonify({"mensaje": f"Intervalo de exploración actualizado a {nuevo_intervalo} segundos"})

@app.route('/topologia', methods=['DELETE'])
def detener_demonio():
    global demonio_activo

    # Solo detiene el demonio si está activo
    if demonio_activo:
        demonio_activo = False
        return jsonify({"mensaje": "Demonio detenido"})
    else:
        return jsonify({"mensaje": "El demonio ya estaba detenido"})

if __name__ == '__main__':
    app.run(debug=True, port=8081)


@app.route('/topologia/grafica')
def grafico_red():
    # Definir la URL de la API de GNS3 (ajusta según sea necesario)
    url_nodos = "http://localhost:3080/v2/projects/4620dc5a-e9fb-4199-baca-ace12e46bf97/nodes"
    url_enlaces = "http://localhost:3080/v2/projects/4620dc5a-e9fb-4199-baca-ace12e46bf97/links"

    # Hacer solicitudes GET a la API de GNS3
    respuesta_nodos = requests.get(url_nodos)
    respuesta_enlaces = requests.get(url_enlaces)

    # Extraer la información de la respuesta de la API
    data_nodos = respuesta_nodos.json()
    data_enlaces = respuesta_enlaces.json()

    # Crear listas de nodos y enlaces
    nodos = [nodo['name'] for nodo in data_nodos]
    enlaces = [(enlace['nodes'][0]['node_id'], enlace['nodes'][1]['node_id']) 
               for enlace in data_enlaces if 'nodes' in enlace]

    # Crear un diccionario de mapeo de nodos
    mapeo_nodos = {nodo['node_id']: nodo['name'] for nodo in data_nodos}

    # Traducir identificadores de nodo a nombres de nodo en los enlaces
    enlaces_traducidos = [(mapeo_nodos[src], mapeo_nodos[dest]) 
                          for src, dest in enlaces if src in mapeo_nodos and dest in mapeo_nodos]

    # Crear un gráfico de la red
    G = nx.Graph()

    # Añadir nodos y enlaces al gráfico
    G.add_nodes_from(nodos)
    G.add_edges_from(enlaces_traducidos)

    # Configurar el gráfico
    plt.figure(figsize=(10, 8))
    nx.draw(G, with_labels=True, node_color='skyblue', node_size=700, font_size=10)

    # Guardar el gráfico en un buffer en lugar de mostrarlo
    img_buffer = io.BytesIO()
    plt.savefig(img_buffer, format='png')
    img_buffer.seek(0)

    # Enviar la imagen como respuesta
    return send_file(img_buffer, mimetype='image/png')
        
@app.route('/routes')
def obtener_router(ip):
    topology_scan.obtener_interfaz()

@app.route('/routes/<ip>')
def obtener_router_especifico(ip):
    topology_scan.obtener_interfaz(ip)


if __name__ == '__main__':
    app.run(debug=True, port=8081)
