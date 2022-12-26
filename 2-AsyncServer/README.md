# Grupo 04: Redes y sistemas distribuidos

### Decisiones de diseño tomada:
    # asyncserver.py:
        Se encarga de realizar la conexión y desconexión, el envío y recepción
        de datos por parte de los clientes.
        Para el manejo de clientes se utiliza una lista de clientes.

    # constants.py:
        Variables globales del programa.

    # connection.py:
        recive: Recibe datos mediante la función reciv().
        response: Arma el mensaje para enviarlo.
        handle: Se encarga de verificar los comandos enviados por el cliente.
            También verifica si el cliente se desconectó de forma imprevista.
        send: Se encarga de enviar los datos.
        outputIsEmpty: Verifica si el buffer está vacío.
        closing: Cierra la conexión con el cliente.

### Dificultades:
    1) Darnos cuenta que en test el "code_ok" esta con minúscula, y como las 
constantes por convensión van con mayúsculas, en nuestro constast.py lo teníamos
como "CODE_OK".
    2) Manejar las conexiones inesperadas (CTRL+C o caída del cliente por x 
motivo).
    Lo solucionamos agregando la siguiente condición:
         if command == '' or command == "\xff\xf4\xff\xfd\x06":
            self.quit()
