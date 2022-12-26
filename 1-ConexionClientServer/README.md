# Grupo 04: Redes y sistemas distribuidos

### Decisiones de diseño tomada:
-Se decidio que era necesaria una variable "connected" para determinar
si el servidor se encontraba conectado a un cliente.

-Al recibir un mensaje del cliente se lo coloca en la cola de comandos.

-Se toma el comando hasta un EOL y dejando el resto del string disponible
para seguir agregando cosas.

-Se utiliza la funcion 'partition' por que es muy util y facil para
cumplir el objetivo

### Estructura del servidor
-Se crea un socket y se lo conecta para luego escuchar mensajes.


