# Requisitos generales del proyecto final de Administración de

## Servicios en Red (primera presentación).
### Objetivo
Desarrollar una API que ofrezca un conjunto de herramientas para la gestión de una red
de cómputo mediante Python en una arquitectura de transferencia de estado
representacional o REST.
## Características y funciones
### Características generales
1. Comunicarse con los dispositivos de red de forma segura usando SSH.
2. Debe de gestionar claves RSA y cifrado de mensajes usando SSH.
3. Cuando se hace una solicitud vía URL a un dispositivo, interfaz o cualquier otro elemento que depende de su presencia en la topología y no existe, debe de devolver un código de HTTP 404.
## Funciones
1. Generar una representación gráfica de la topología de una red, detectándola de forma dinámica.
2. CRUD de usuarios en los dispositivos de red, globales y por dispositivo, con gestión de los permisos y accesos vía SSH.
3. Obtener la información general de los enrutadores en la red.
4. Obtener la información general por interfaz del enrutador.
##  Características de la revisión
La topología sobre la que se revisará el software es dinámica, es decir, que se pedirá que
cambie durante la revisión

Los dispositivos de la red de prueba tendrán únicamente definido las direcciones IP de las
interfaces, algún enrutamiento dinámico y un usuario con permisos de administración y
acceso por telnet.
### Primera presentación.
Implementar las siguientes funciones de la API-REST:

|  Funcion  |  Ruta  |  Get |  Post |  Put |  Delete | 
|---|---|---|---|---|---|
| CRUD Usuarios                |  /usuarios                      | Regresar json con todos los usuarios existentes en los routers, incluyendo nombre, permisos y dispositivos donde existe (URL a routers donde exista cada usuario).  | Agregar un nuevo usuario a todos los routers, regresar json con la misma información de GET pero del usuario agregado.  | Actualizar un usuario en todos los routers, regresar json con la misma información de GET pero del usuario actualizado.  | Eliminar usuario común a todos los routers, recuperar json con la misma información de GET pero del usuario eliminado.|
|  Enrutadores                 |  /routes o /routes/*hostname*   | Regresa la información general de todos los routers de la topología. Incluyendo Nombre, IP loopback, IP administrativa, rol, empresa, Sistema operativo y ligas a las interfaces activas. **o** Regresa en formato json la información general del router definido. Incluyendo Nombre, IP loopback, IP administrativa, rol, empresa, Sistema operativo y ligas a las interfaces activas.  |  *  |  *  | * |
|  Interfaces de Routers       |  /routes/*hostname*/interfaces  | Regresa en formato json la información general de la interfaz del router definido. Incluyendo tipo, número, IP, mascara de rubred, estado y la liga al router que está conectado, si es el caso  |  * |  * |  *  |
|  CRUD usuarios por enrutador |  /routers/*hostname*/usuarios/  | Regresar json con los usuarios existentes en el router específico, incluyendo nombre y permisos  | Agregar un nuevo usuario al router específico, regresar json con la misma información de GET pero del usuario agregado  | Actualizar un nuevo usuario al router específico, regresar json con la misma información de GET pero del usuario actualizado.  | Eliminar usuario común a todos los routers, recuperar json con la misma información de GET pero del usuario eliminado.  |
|  Detectar Topologia          |  /topologia                     | Regresar json con los routers existentes en la topología y ligas a sus routers vecinos  |  Activa un demonio que cada 5 minutos explora la red para detectar cambios en la misma | Permite cambiar el intervalo de tiempo en el que el demonio explora la topología.  | Detiene el demonio que explora la topologia.  |
|  Grafica de Topologia        |  /topologia/grafica             | Regresa un archivo en algún formato gráfico donde se pueda visualizar la topología existente.  |  * | *  |  * |
