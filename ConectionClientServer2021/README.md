# Informe #
Como nuestro objetivo para este laboratorio es crear una comunicación cliente/servidor por medio de la programación de sockets, 
desde la perspectiva del servidor, necesitamos una estructura del servidor que este bien modularizado, en donde por un lado 
tenemos el archivo server.py que se encarga de crear el socket servidor y aceptar una conexión con el cliente, en el archivo 
client.py lo que hace es enviarle pedidos al servidor y para el archivo connection.py nos encargarnos de recibir lo que el cliente 
manda, lo procesamos y le enviamos una respuesta.
En cuanto las decisiones de diseño tomadas en connection.py, dentro del handle manejamos los pedidos de diferente comandos que nos 
realiza el servidor, también verificamos distintos tipos de errores que pueden llegar a surgir, fuera del handle implementamos un 
método para los distintos tipos de errores, el cual completa la respuesta de error obteniendo datos del archivo constants.py, y 
otro método para la función send así este no quedaba demasiado largo en cada linea de código que lo utilizábamos.
Una de las dificultades que tuvimos fue que no sabíamos que el test_multiple_commands cerraba la conexión sin que el cliente 
mandara un quit, entonces nuestro servidor nunca se daba cuenta que la conexión había sido cerrada y por ende en nuestro código 
nunca cerrábamos la conexión del servidor.

## Preguntas ##
- 1.¿Qué estrategias existen para poder implementar este mismo servidor pero con capacidad de atender múltiples clientes 
simultáneamente? Investigue y responda brevemente qué cambios serían necesario en el diseño del código.

Para implementar este mismo servidor pero con capacidad de atender múltiples clientes simultáneamente necesitamos importar la 
librería select y utilizar la función o metodo poll() que nos va devolver un pollerObject, luego registrar nuestro socket servidor 
dentro del pollerObjet con el método register (pollerObject.register(serverSocket, POLLIN) donde POLLIN es la entrada de lista). 
Despues utilizar el método poll del objeto pollerObjet para diferenciar los tipos de eventos que ingresan, en el cual hay 3 
posibles casos:

\* Si el descriptor de archivo pertenece a nuestro servidor aceptamos nuevas conexiones la cual registramos dentro de nuestro 
pollerObject (pollerObject.register(clientSocket, POLLIN))

\* Ocurre un evento y es de tipo POLLIN, recibimos el comando del cliente y lo procesamos y cambamos el evento a tipo POLLOUT.

\* Ocurre un evento y es de tipo POLLOUT, respondemos al cliente y si el cliente se despide cerramos la conexión y lo sacamos del 
registro de nuestro pollerObject o 	lo volvemos a cambiar a un evento de tipo POLLIN para recibir una nueva petición del cliente. 



- 2.Pruebe ejecutar el servidor en una máquina del laboratorio, mientras utiliza el cliente desde otra, hacia la ip de la máquina 
servidor. ¿Qué diferencia hay si se corre elservidor desde la IP “localhost”, “127.0.0.1” o la ip “0.0.0.0”?

La diferencia entre 0.0.0.0 y 127.0.0.1 es que la dirección 127.0.0.1 se conoce como home, localhost o dirección de loopback. Otra 
confusión muy común es la de asumir que 127.0.0.1 se refiere a tu propia computadora, en realidad, 127.0.0.1 es una dirección 
designada para proveer una interfaz IP funcional y completa dentro de tu misma computadora, sin importar cual es la configuración 
de la red exterior. Todo el tráfico que se envía a 127.0.0.1 es inmediatamente recibido. Una manera de visualizar el concepto es 
imaginando un mini segmento de red que "vive" dentro de tu computadora y que permite que dispositivos, procesos y sockets se 
puedan conectar a tu máquina.
Por el otro lado, la dirección 0.0.0.0 no es una dirección IP válida para asignarla a una interfaz de red, de hecho, ninguna 
dirección IP en la subnet 0.0.0.0/8 es una dirección valida (es decir, cualquier dirección que empiece con 0.0.0.x)
La dirección 0.0.0.0 no puede ser utilizada como origen de ningún paquete IP, a menos de que la computadora no sepa su propia 
dirección IP e intente obtener una dirección propia (DHCP es un ejemplo de éste escenario)
Si 0.0.0.0 se utiliza en una tabla de rutas, ésta dirección identifica la puerta de enlace predeterminada. La ruta designada como 
0.0.0.0 es la ruta que se utiliza cuando no existe ninguna otra ruta disponible para llegar a la dirección IP del destinatario.
Finalmente, cuando un servicio escucha por conexiones en la dirección 0.0.0.0 significa que el servicio escuchará conexiones en 
todas las direcciones IP disponibles en la computadora.
