#!/usr/bin/env python
# encoding: utf-8
# Revisión 2014 Carlos Bederián
# Revisión 2011 Nicolás Wolovick
# Copyright 2008-2010 Natalia Bidart y Daniel Moisset
# $Id: server.py 656 2013-03-18 23:49:11Z bc $

import optparse
import socket
import connection
import select
from constants import *


class Server(object):
    """
    El servidor, que crea y atiende el socket en la dirección y puerto
    especificados donde se reciben nuevas conexiones de clientes.
    """

    # Creamos un socket, lo conectactamos mediante la fuoncion bind()
    # para luego ponerlo a escuchar mensajes con la funcion listen()

    # Tambien se declaran una variable connected para determinar si
    # el servidor se encuentra conectado a un cliente

    def __init__(self, addr=DEFAULT_ADDR, port=DEFAULT_PORT,
                 directory=DEFAULT_DIR):
        print "Serving %s on %s:%s." % (directory, addr, port)
        # FALTA: Crear socket del servidor, configurarlo, asignarlo
        # a una dirección y puerto, etc.
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # para que no nos bloqué el puerto y podamos reutilizarlo
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.s.bind((addr, port))
        self.s.listen(5)
        self.directory = directory
        #   Aceptamos una conexion...

    def serve(self):
        """
        Loop principal del servidor. Se acepta una conexión a la vez
        y se espera a que concluya antes de seguir.
        """
        poll = select.poll()
        poll.register(self.s, select.POLLIN)
        clients = {}
        while True:
            events = poll.poll()
            for fileno, event in events:
                # El descriptor de archivo pertenece al servidor
                if fileno == self.s.fileno():
                    # Conectamos un socket de cliente
                    client_socket, client_address = self.s.accept()
                    client_socket.setblocking(0)
                    # Registramos el evento
                    poll.register(client_socket, select.POLLIN)
                    # Creamos un objeto conexion para cada cliente que se
                    # conecta y completamos los datos
                    con = connection.Connection(client_socket, self.directory)
                    # Ponemos el nuevo cliente en una lista de clientes
                    # respresentado por su descriptor de archivo
                    clients[client_socket.fileno()] = con
                    print('New client: ' + str(client_address))
                elif event & select.POLLIN:
                    con = clients[fileno]
                    command = con.recive()
                    con.handle(command)
                    print('Client %s says: %s' % (fileno, command))
                    if not con.outputIsEmpty():
                        poll.modify(fileno, select.POLLOUT)
                elif event & select.POLLOUT:
                    con = clients[fileno]
                    con.send()
                    if con.outputIsEmpty() and con.remove:
                        con.closing()
                        poll.unregister(fileno)
                        del clients[fileno]
                    elif con.outputIsEmpty():
                        poll.modify(fileno, select.POLLIN)


def main():
    """Parsea los argumentos y lanza el server"""

    parser = optparse.OptionParser()
    parser.add_option(
        "-p", "--port",
        help=u"Número de puerto TCP donde escuchar", default=DEFAULT_PORT)
    parser.add_option(
        "-a", "--address",
        help=u"Dirección donde escuchar", default=DEFAULT_ADDR)
    parser.add_option(
        "-d", "--datadir",
        help=u"Directorio compartido", default=DEFAULT_DIR)

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
