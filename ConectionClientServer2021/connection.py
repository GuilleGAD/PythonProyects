# encoding: utf-8
# Revisión 2019 (a Python 3 y base64): Pablo Ventura
# Copyright 2014 Carlos Bederián
# $Id: connection.py 455 2011-05-01 00:32:09Z carlos $

import socket
from constants import *
from base64 import b64encode
import os


class Connection(object):
    """
    Conexión punto a punto entre el servidor y un cliente.
    Se encarga de satisfacer los pedidos del cliente hasta
    que termina la conexión.
    """

    def __init__(self, socket, directory):
        self.socket_client = socket
        self.directory = directory
        self.command_request = ''
        self.command_respond = ''
        self.is_connected = True

    def handle(self):
        """
        Atiende eventos de la conexiÃ³n hasta que termina.
        """
        # Mientras el clilentes esté conectado
        while self.is_connected:
            # flag se utiliza para recibir hasta que llegue un /r/n
            flag = True
            self.command_request = ''
            while flag:
                if EOL not in self.command_request:
                    # se utiliza try para evitar bloqueos si el cliente se
                    # desconecta de forma repentina.
                    # tambien para evitar que venga algun caracter que no
                    # sea de tipo ASCII (como por ej caracteres chinos)
                    try:
                        self.command_request += self.socket_client.recv(
                            4096).decode('ASCII')
                    except socket.error:
                        print("El cliente perdió la conexión")
                        self.is_connected = False
                        self.socket_client.close()
                        break
                    except ValueError:
                        self.CODE_MESSAGE(BAD_REQUEST)
                        self.fatal_error()
                        break
                # se procesa el comando enviado
                else:
                    flag = False
                    # se divide los comandos por el terminador /r/n
                    # eso devuelve una lista de comandos
                    list_n_commands = self.command_request.split(EOL)
                    # iteramos sobre la lista de comandos
                    for command in list_n_commands:
                        if command != '':
                            # si hay un /n en el comando es un error
                            if '\n' in command:
                                self.CODE_MESSAGE(BAD_EOL)
                                self.fatal_error()
                                # se cierra la conexión con el cliente
                                break
                            # protegemos para que el cliente no acceda a otros
                            # directorios
                            if '../' in command:
                                self.CODE_MESSAGE(FILE_NOT_FOUND)
                                self.send()
                                # se tira el error y se vuelve al principio del
                                # ciclo para esperar nuevo comando
                                continue
                            # separamos el comando y sus argumentos
                            command_in_parts = command.split(' ')
                            if command_in_parts[0] == 'get_file_listing':
                                # get_file_listing no debe contar con
                                # argumentos
                                if len(command_in_parts) == 1:
                                    self.get_file_listing()
                                else:
                                    self.CODE_MESSAGE(INVALID_ARGUMENTS)
                            elif command_in_parts[0] == 'get_metadata':
                                # get_metadata solo debe contar con 1
                                # argumentos
                                if len(command_in_parts) == 2:
                                    self.get_metadata(command_in_parts[1])
                                else:
                                    self.CODE_MESSAGE(INVALID_ARGUMENTS)
                            elif command_in_parts[0] == 'get_slice':
                                # get_slice solo debe contar con 3 argumentos
                                if len(command_in_parts) == 4:
                                    self.get_slice(
                                        command_in_parts[1],
                                        command_in_parts[2],
                                        command_in_parts[3])
                                else:
                                    self.CODE_MESSAGE(INVALID_ARGUMENTS)
                            elif command_in_parts[0] == 'quit':
                                # quit no debe contar con argumentos
                                if len(command_in_parts) == 1:
                                    self.quit()
                                else:
                                    self.CODE_MESSAGE(INVALID_ARGUMENTS)
                            # en caso de llegar cualquier otra cosa, se
                            # devuelve el error adecuado
                            else:
                                self.CODE_MESSAGE(INVALID_COMMAND)
                # Si comando es != '' significa que hubo un error y debe
                # ser enviado
                if self.command_respond != '':
                    self.send()

    def get_file_listing(self):
        # se utiliza try porque es una llamada al sistema y se puede dar
        # la posibilidad de no tener permisos adecuados para leer un directorio
        # entre otros posibles errores del sistema
        try:
            self.CODE_MESSAGE(CODE_OK)
            for file in os.listdir(self.directory):
                self.command_respond += file + EOL
            self.command_respond += EOL
            self.send()
        except IOError:
            # error en caso de problemas en llamadas al sistema
            self.CODE_MESSAGE(INTERNAL_ERROR)
            self.fatal_error()

    def get_metadata(self, file):
        # se utiliza try porque es una llamada al sistema y se puede dar
        # la posibilidad de no tener permisos adecuados para leer un archivo
        # entre otros posibles errores del sistema
        try:
            path = os.path.join(self.directory, file)
            # se verifica si el archivo existe
            if os.path.exists(path):
                self.CODE_MESSAGE(CODE_OK)
                # se obtiene el tamaño del archivo
                file_size = str(os.path.getsize(path))
                self.command_respond += file_size + EOL
            else:
                # error en caso de que el archivo no exista
                self.CODE_MESSAGE(FILE_NOT_FOUND)
            self.send()
        except IOError:
            # error en caso de problemas en llamadas al sistema
            self.CODE_MESSAGE(INTERNAL_ERROR)
            self.fatal_error()

    def get_slice(self, file, offset, size):
        if offset.isnumeric() and size.isnumeric():
            offset_ = int(offset)
            size_ = int(size)
            # se utiliza try porque es una llamada al sistema y se
            # puede dar la posibilidad de no tener permisos adecuados
            # para leer un archivo entre otros posibles errores del
            # sistema
            try:
                path = os.path.join(self.directory, file)
                # se verifica si el archivo existe
                if os.path.exists(path):
                    # se abre el archivo de forma de lectura binaria
                    file = open(path, 'rb')
                    file_size = os.path.getsize(path)
                    # se verifica si el offset mas el size solicitado es menor
                    # que el tamaño total del archivo
                    if offset_ + size_ <= file_size:
                        self.CODE_MESSAGE(CODE_OK)
                        # nos posicionamos desde donde queremos leer
                        file.seek(offset_)
                        # se lee el archivo
                        read = file.read(size_)
                        # se arma la respuesta transformando la lectura que
                        # se hizo en base64
                        self.command_respond += str(
                            b64encode(read).decode('ASCII')) + EOL
                    else:
                        # error en caso de exceder el tamaño total
                        self.CODE_MESSAGE(BAD_OFFSET)
                    file.close()
                else:
                    # error en caso de que el archivo no exista
                    self.CODE_MESSAGE(FILE_NOT_FOUND)
                self.send()
            except IOError:
                # error en caso de problemas en llamadas al sistema
                self.CODE_MESSAGE(INTERNAL_ERROR)
                self.fatal_error()
        else:
            # error en caso de que los argumentos sean invalidos
            self.CODE_MESSAGE(INVALID_ARGUMENTS)
            self.send()

    def quit(self):
        # se modifica is_connected para que finalice el ciclo while
        # del handle
        self.is_connected = False
        # se limpis el request
        self.command_request = ''
        # se genera el mensaje de error
        self.CODE_MESSAGE(CODE_OK)
        self.send()
        # se cierra la conexión del socket
        self.socket_client.close()

    '''
    El método send() se encarga de realizar el envío de la respuesta formada en
    self.command_respond, y luego lo limpia al atributo
    '''

    def send(self):
        # utilizamos try para evitar bloqueos si el cliente se desconecta
        # de forma repentina
        try:
            self.socket_client.send(self.command_respond.encode())
            self.command_respond = ''
        except socket.error:
            print("El cliente perdió la conexión")
            self.is_connected = False
            self.socket_client.close()

    '''
    El método fatal_error() se encarga de realizar el envío del error
    correspondiente setear is_conected en false para finalizar el ciclo
    while dentro del hande y cerrar la conexión del socket
    '''

    def fatal_error(self):
        self.send()
        self.is_connected = False
        self.socket_client.close()

    """
    Método que se encarga de armar el mensaje de error a traves
    del código pasado por parámetro
    """

    def CODE_MESSAGE(self, codeError):
        self.command_respond = str(codeError) + ' ' + \
            error_messages[codeError] + EOL
