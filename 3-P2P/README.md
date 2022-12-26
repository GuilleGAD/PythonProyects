# Grupo 04: Redes y sistemas distribuidos

## Estructuracion del servidor:
    El servidor recibe un pedido HTTP de un cliente, se procesa ese pedido para trabajar con conexiones no persistentes. Una vez modificado el pedido, se redirecciona el pedido al servidor web donde esta alojada la pagina solicitada. El servidor web recibe el pedido y envia los datos correspondientes, el servidor toma esos datos y los envia al cliente que los solicito.

## Decisiones de diseño tomada:
###    connection.py:
        -En la clase Connection se implementaron los metodos tal como estaban especificados.
        -Para la clase RequestHandlerTask se implementaron funciones auxiliares para obtener, modificar y rearmar los encabezados HTTP

###    proxy.py:
        -Se implementan los metodos tal como se especificaron.
        -Maneja las conexiones transparentemente de si es un cliente o un servidor.

## Dificultades:
    1) Entender el flujo de las comunicaciones entre los distintos actores, i.e en que momento debiamos direccionar los datos al servidor o al cliente.
    2) Identificar en que momentos debiamos cerrar una conexion.
    3) En el metodo connect del modulo proxy.py, nos costo mucho entender como abstraernos para poder usar el mismo metodo para conectarnos tanto al cliente como al servidor.