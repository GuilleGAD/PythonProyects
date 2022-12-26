# encoding: utf-8
# $Rev: 512 $

"""
Módulo que provee manejo de conexiones genéricas
"""

from socket import error as socket_error
import logging
from config import *
from queue import Queue, ProtocolError
import os
import re

# Estados posibles de la conexion
DIR_READ = +1   # Hay que esperar que lleguen más datos
DIR_WRITE = -1  # Hay datos para enviar


class Connection(object):
    """Abstracción de conexión. Maneja colas de entrada y salida de datos,
    y una funcion de estado (task). Maneja tambien el avance de la maquina de
    estados.
    """

    def __init__(self, fd, address=''):
        """Crea una conexión asociada al descriptor fd"""
        self.socket = fd
        self.task = None  # El estado de la maquina de estados
        self.input = Queue()
        self.output = Queue()
        self.remove = False  # true para pedir al proxy que desconecte
        self.address = address

    def fileno(self):
        """
        Número de descriptor del socket asociado.
        Este metodo tiene que existir y llamarse así para poder pasar
        instancias de esta clase a select.poll()
        """
        return self.socket.fileno()

    def direction(self):
        """
        Modo de la conexión, devuelve uno de las constantes DIR_*; también
        puede devolver None si el estado es el final y no hay datos para
        enviar.
        """
        # COMPLETAR
        if self.output.data != '':
            return DIR_WRITE
        elif self.task is None:
            return None
        else:
            return DIR_READ

    def recv(self):
        """
        Lee datos del socket y los pone en la cola de entrada.
        También maneja lo que pasa cuando el remoto se desconecta.
        Aqui va la unica llamada a recv() sobre sockets.
        """
        data = self.socket.recv(MAX_PACKAGE_LEN)
        self.input.put(data)

    def send(self):
        """Manda lo que se pueda de la cola de salida"""
        # COMPLETAR
        packet_len = self.socket.send(self.output.data)
        self.output.clear()

    def close(self):
        """Cierra el socket. OJO que tambien hay que avisarle al proxy que nos
        borre.
        """
        self.response(CODE_OK)
        self.socket.close()
        self.remove = True
        self.output.clear()

    def send_error(self, code, msg):
        """Funcion auxiliar para mandar un mensaje de error"""
        logging.warning("Generating error response %s [%s]",
            code, self.address)
        self.output.put("HTTP/1.1 %d %s\r\n" % (code, msg))
        self.output.put("Content-Type: text/html\r\n")
        self.output.put("\r\n")
        self.output.put("<body><h1>%d ERROR: %s</h1></body>\r\n" % (code, msg))
        self.remove = True


class Forward(object):
    """Estado: todo lo que venga, lo retransmito a la conexión target"""

    def __init__(self, target):
        self.target = target

    def apply(self, connection):
        # COMPLETAR
        # Considerar que hacer si el otro cierra la conexion
        # (la cola de entrada va a estar vacia)
        # Esto puede devolver
        #  - self, cuando hay que seguir retransmitiendo
        #  - None cuando no hay que hacer mas nada con esta conexion en el
        # futuro
        self.target.output.data = connection.input.data
        connection.input.clear()
        return self


class RequestHandlerTask(object):

    def __init__(self, proxy):
        self.proxy = proxy
        ### Agregar cosas si hace falta para llevar estado interno.
        # Puede que les convenga llevar
        # self.host = None
        # self.url = None

    def apply(self, connection):
        self.connection = connection
        # COMPLETAR
        # Parsear lo que se vaya podiendo de self.input (utilizar los metodos
        # de Queue). Esto puede devolver
        # - None en caso de error, por ejemplo:
        #    * hubo un error de parseo
        #    * la url no empieza con http:// (es decir, no manejamos este
        # protocolo) (error 400 al cliente)
        #    * Falta un encabezado Host y la URL del pedido tampoco tiene host
        # (error 400 al cliente)
        #    * Nos pidieron hacer proxy para algo que no esta en la
        # configuracion (error 403 al cliente)
        # - Una instancia de Forward a una nueva conexion si se puede proxyar
        #    En este caso también hay que crear la conexion y avisarle al
        # Proxy()

        try:
            metodo, url, protocolo = connection.input.read_request_line()
        except ProtocolError, error:
            connection.send_error(error.code, error.message)
            return None

        try:
            if not connection.input.parse_headers():
                return self
        except ProtocolError as error:
            # Pone en la cola de salida de connection mensaje de error
            connection.send_error(error.code, error.message)
            return None

        match = re.match('http:\/\/([^\/]*)', url)
        if match is None:
            for header in headers:
                if header[0] == 'Host':
                    servername = header[1]
            if servername is None:
                connection.send_error(BAD_URL)
                return None
        else:
            servername = match.group(1)

        target = self.proxy.connect(servername)
        target.task = Forward(connection)
        #Buscamos el header Connection para que no mantenga la
        #conexión
        self.modify_headers('Connection', 'close')
        to_host = self.get_header('Host')
        #Armamos un request para mandar
        request_to_send = self.reassamble_request(metodo, url, protocolo)
        target.output.put(request_to_send)
        connection.input.clear()
        forward = Forward(target)
        return forward

    def get_header(self, header):
        index = -1
        for i, (header_name, header_value) in enumerate(self.connection.input.headers):
            if header_name == header:
                index = i
        return self.connection.input.headers[index][1]

    #Modificamos los headers antes de mandar el pedido al servidor
    def modify_headers(self, header, value):
        index = -1
        #Buscamos para ver si está en la lista
        for i, (header_name, header_value) in enumerate(self.connection.input.headers):
            if header_name == header:
                index = i
        if not index == -1:
            self.connection.input.headers[index][1] = value
        else:
            self.connection.input.headers.appenden([header, value])

    def reassamble_request(self, method, url, protocol):
        reassambled_request = ''
        reassambled_request += method + ' ' + url + ' ' + protocol + SEPARATOR
        for i in self.connection.input.headers:
            r = reassambled_request
            reassambled_request = r + i[0] + ':' + i[1] + SEPARATOR
        reassambled_request += SEPARATOR
        return reassambled_request
