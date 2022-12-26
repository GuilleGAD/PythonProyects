# encoding: utf-8
import socket
import select
import logging
import os
from config import *
from connection import Connection, DIR_READ, DIR_WRITE, RequestHandlerTask


class Proxy(object):
    """Proxy HTTP"""

    def __init__(self, port, hosts):
        """
        Inicializar, escuchando en port, y sirviendo los hosts indicados en
        el mapa `hosts`
        """

        # Conexión maestra (entrante)
        master_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        master_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        master_socket.bind(('', port))
        logging.info("Listening on %d", port)
        master_socket.listen(5)
        self.host_map = hosts
        self.connections = []
        self.master_socket = master_socket
        # AGREGAR estado si lo necesitan

    def run(self):
        """Manejar datos de conexiones hasta que todas se cierren"""
        while True:
            self.handle_ready()
            p = self.polling_set()
            # poll
            events = p.poll()
            self.handle_events(events)
            self.remove_finished()
            # COMPLETAR: Quitar conexiones que pidieron que las cierren
            #  - Tienen que tener el remove prendido
            #  - OJO: que pasa si la conexion tiene cosas todavía en cola de
            # salida?
            #  - Acordarse de usar el metodo close() de la conexion

    def polling_set(self):
        """
        Devuelve objeto polleable, con los eventos que corresponden a cada
        una de las conexiones.
        Si alguna conexión tiene procesamiento pendiente (que no requiera
        I/O), realiza ese procesamiento antes de poner la conexión en el
        conjunto.
        """
        p = select.poll()
        # COMPLETAR. Llamadas a register que correspondan, con los eventos
        # que correspondan
        p.register(self.master_socket.fileno(), select.POLLIN)
        for con in self.connections:
            if con.direction() == DIR_WRITE:
                p.register(con.fileno(), select.POLLOUT)
            elif con.direction() == DIR_READ:
                p.register(con.fileno(), select.POLLIN)
            elif con.direction() is None:
                p.unregister(conn.fileno())
                conn.close()
        return p

    def connection_with_fd(self, fd):
        """
        Devuelve la conexión con el descriptor fd
        """
        for con in self.connections:
            if con.fileno() == fd:
                return con
        return None

    def handle_ready(self):
        """
        Hace procesamiento en las conexiones que tienen trabajo por hacer.
        Es decir, las que estan leyendo y tienen datos en la cola de entrada
        """
        for c in self.connections:
            # Hacer avanzar la maquinita de estados
            if c.input.data:
                c.task = c.task.apply(c)

    def handle_events(self, events):
        """
        Maneja eventos en las conexiones. events es una lista de pares
        (fd, evento)
        """
        # COMPLETAR:
        #   - Segun los eventos que lleguen hay que:
        #       * Llamar a self.accept_new() si hay una conexion nueva
        #       * Llamar a c.send / c.recv / c.close en las conexiones
        # que corresponda
        for fileno, event in events:
            if event & select.POLLIN:
                if fileno == self.master_socket.fileno():
                    self.accept_new()
                else:
                    conn = self.connection_with_fd(fileno)
                    conn.recv()
            elif event & select.POLLOUT:
                conn = self.connection_with_fd(fileno)
                conn.send()
            elif event & select.POLLHUP:
                conn = self.connection_with_fd(fileno)
                conn.close()

#pollhup
    def accept_new(self):
        """Acepta una nueva conexión"""
        # COMPLETAR
        #  - Crea una nueva instancia de conexion y la agrega.
        #  - le setea la tarea a RequestHandlerTask(self)

        client_socket, client_address = self.master_socket.accept()
        client_socket.setblocking(0)
        connection = Connection(client_socket, client_address)
        connection.task = RequestHandlerTask(self)
        self.append(connection)

    def remove_finished(self):
        """
        Elimina conexiones marcadas para terminar
        """
        # COMPLETAR
        for con in self.connections:
            if con.remove:
                self.connections.remove(con)

    def connect(self, hostname):
        """
        Establece una nueva conexion saliente al hostname dado. El
        hostname puede tener la forma host:puerto ; si se omite el
        :puerto se asume puerto 80.
        Aqui esta la unica llamada a connect() del sistema. No
        preocuparse por el caso de connect() bloqueante
        """
        if ":" in hostname:
            host, port = hostname.split(':')
        else:
            host, port = hostname, 80
        try:
            address = self.host_map[host]
        except:
                ip = socket.gethostbyname(host)
                self.host_map[host] = [ip]
                address = self.host_map[host]
        print self.host_map[host]
        if len(address) > 1:
            ip = address[1]
        ip = address[0]
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((ip, port))
        conn = Connection(s, ip)
        if not conn in self.connections:
            self.connections.append(conn)
        return conn

    def append(self, c):
        self.connections.append(c)
