#!/usr/bin/env python
# encoding: utf-8
# Revisión 2019 (a Python 3 y base64): Pablo Ventura
# Revisión 2014 Carlos Bederián
# Revisión 2011 Nicolás Wolovick
# Copyright 2008-2010 Natalia Bidart y Daniel Moisset
# $Id: server.py 656 2013-03-18 23:49:11Z bc $

import optparse
import socket
import connection
from constants import *
import os


class Server(object):
    """
    El servidor, que crea y atiende el socket en la dirección y puerto
    especificados donde se reciben nuevas conexiones de clientes.
    """

    def __init__(self, addr=DEFAULT_ADDR, port=DEFAULT_PORT,
                 directory=DEFAULT_DIR):
        print("Serving %s on %s:%s." % (directory, addr, port))
        # FALTA: Crear socket del servidor, configurarlo, asignarlo
        # a una dirección y puerto, etc.
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # guardamos IP y Puerto
        server_address = (addr, port)
        self.s.bind(server_address)
        self.directory = directory
        self.s.listen(1)

    def serve(self):
        """
        Loop principal del servidor. Se acepta una conexión a la vez
        y se espera a que concluya antes de seguir.
        """
        # Se utiliza try porque es una llamada al sistema y se puede dar
        # la posibilidad de no tener permisos adecuados para crear directorio
        # entre otros posibles errores del sistema
        try:
            # Se verifica si el directorio existe, sino lo crea
            if not os.path.exists(self.directory):
                os.mkdir(self.directory)

            cliente = 1
            while True:
                # FALTA: Aceptar una conexión al server, crear una
                # Connection para la conexión y atenderla hasta que termine.
                print('Esperando cliente')
                conn, addr = self.s.accept()
                print('Se conecto el cliente numero ' + str(cliente))
                c = connection.Connection(conn, self.directory)
                c.handle()
                print('Se desconectó el cliente numero ' + str(cliente))
                cliente += 1
        except IOError:
            print(str(INTERNAL_ERROR) + ' ' +
                  error_messages[INTERNAL_ERROR])


def main():
    """Parsea los argumentos y lanza el server"""

    parser = optparse.OptionParser()
    parser.add_option(
        "-p", "--port",
        help="Número de puerto TCP donde escuchar", default=DEFAULT_PORT)
    parser.add_option(
        "-a", "--address",
        help="Dirección donde escuchar", default=DEFAULT_ADDR)
    parser.add_option(
        "-d", "--datadir",
        help="Directorio compartido", default=DEFAULT_DIR)

    options, args = parser.parse_args()
    if len(args) > 0:
        parser.print_help()
        sys.exit(1)
    try:
        port = int(options.port)
    except ValueError:
        sys.stderr.write(
            "Numero de puerto invalido: %s\n" % repr(options.port))
        parser.print_help()
        sys.exit(1)

    server = Server(options.address, port, options.datadir)
    server.serve()


if __name__ == '__main__':
    main()
