from flask import Flask, jsonify, request
import paramiko
import time
import topology_scan

app = Flask(__name__)

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

# Ruta para escanear toda la topologia
@app.route('/topologia', methods=['GET'])
def topologia():
    topology_scan.scan_all()

# Ruta para obtener info de los routers
@app.route('/routes', methods=['GET'])
def router():
    topology_scan.obtener_router()

# Ruta para obtener la info de un router específico
@app.route('/routes/<ip>', methods=['GET'])
def router_espe(ip):
    topology_scan.obtener_router(Ip=ip)

# Ruta para obtener la info de una interfaz de un router específico
@app.route('/routes/<ip>/interface', methods=['GET'])
def interfaz(ip):
    topology_scan.obtener_interfaz(ip,ip,usuario,contrasena)

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
        comando_agregar_usuario = f'username {nuevo_usuario} privilege {privilegio} password {nueva_contrasena}\n'
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
                comando_agregar_usuario = f'username {nuevo_usuario} privilege {privilegio} password {nueva_contrasena}\n'
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

        
if __name__ == '__main__':
    app.run(debug=True, port=8081)