# encoding: utf-8
# Copyright 2014 Carlos Bederián
# $Id: connection.py 455 2011-05-01 00:32:09Z carlos $

import os
from constants import *


class Connection(object):
    """
    Conexión punto a punto entre el servidor y un cliente.
    Se encarga de satisfacer los pedidos del cliente hasta
    que termina la conexión.
    """

    def __init__(self, socket, directory):
        self.directory = directory
        self.s = socket
        self.datos = ''
        self.address = ''
        self.command = ''
        self.output = []
        self.remove = False
        pass

    # Recibimos datos (un string) desde el cliente
    # y los ponemos en una cola de comandos; leemos hasta un EOL
    # y tomamos el comando, dejando el resto del string disponible
    # para seguir concatenandole cosas. Usamos la función 'partition'
    # porque es muy útil y fácil para cumplir el objetivo.

    def recive(self):
        self.datos += self.s.recv(BLOCK_SIZE)
        return self.datos

    def response(self, code):
        self.output.append(str(code) + ' ' + error_messages[code] + EOL)

    # Parseamos los datos recibidos del cliente y ejecutamos según corresponda.
    # Llamamos a cada función en el parser.

    def handle(self, command):
        """
        Atiende eventos de la conexión hasta que termina.
        """
        if command == '' or command == "\xff\xf4\xff\xfd\x06":
            self.quit()
        while EOL in self.datos:
            command, rest = self.datos.split(EOL, 1)
            self.datos = rest
            command_list = command.split(' ')
            command_list_len = len(command_list)
            if '\n' not in command:
                if command_list[0] == "get_file_listing":
                    if command_list_len == 1:
                        self.get_file_listing()
                    else:
                        self.response(invalid_arguments)

                elif command_list[0] == "get_metadata":
                    if command_list_len == 2:
                        self.get_metadata(command_list[1])
                    else:
                        self.response(invalid_arguments)

                elif command_list[0] == "get_slice":
                    if command_list_len == 4:
                        self.get_slice(command_list[1],
                                       command_list[2], command_list[3])
                    else:
                        self.response(INVALID_ARGUMENTS)

                elif command_list[0] == "quit":
                    if command_list_len == 1:
                            self.quit()
                    else:
                        self.response(INVALID_ARGUMENTS)

                else:
                    self.response(INVALID_COMMAND)
            else:
                self.response(BAD_EOL)

    def get_file_listing(self):
        """
        Envia la lista de archivos disponibles al cliente
        """
        try:
            listdir = os.listdir(self.directory)
        except OSError:
            self.response(INTERNAL_ERROR)
            return
        for i in range(len(listdir)):
            listdir[i] += EOL
        self.response(code_ok)
        self.output.append(''.join(listdir)+EOL)

    def get_metadata(self, filename):
        """
        Envia los metadatos de un archivo al cliente
        """
        # Convertimos el string "filename" en un conjunto y nos fijamos
        # si pertenece al tipo alphanum. El nombre original no se modifica.
        # print 'filename:' + filename
        assert (filename != "")
        setfilename = set(filename)
        is_alpha = setfilename.issubset(alphaset)
        # Si pertenece al conjunto nos fijamos que exista
        # y respondemos con '0 Ok'
        if is_alpha:
            try:
                path = os.path.join(self.directory, filename)
                flag = os.path.exists(path)
            except OSError:
                self.response(INTERNAL_ERROR)
                return
            if flag:
                self.response(code_ok)
                self.output.append(str(os.path.getsize(path)) + EOL)
            else:
                self.response(FILE_NOT_FOUND)
        else:
            self.response(INVALID_ARGUMENTS)

    def get_slice(self, filename, str_offset, str_size):
        """
        Envia una cantidad definida de bytes al cliente
        """
        assert (filename[0] != '/' or filename != "" or str_size != "")
        # Primero chequeamos que los ultimos dos parametros de la funcion sean
        # del tipo numero y luego verificamos si el archivo esta disponible
        try:
            path = os.path.join(self.directory, filename)
            file_exists = os.path.exists(path)
        except OSError:
            self.response(INTERNAL_ERROR)
            return

        if not file_exists:
            self.response(FILE_NOT_FOUND)
            return

        if not (str_offset.isdigit() and str_size.isdigit()):
            self.response(INVALID_ARGUMENTS)
            return

        try:
            size_file = os.path.getsize(path)
        except OSError:
            self.response(INTERNAL_ERROR)
            return
        size = int(str_size)
        offset = int(str_offset)
        flag = (offset + size > size_file) or (offset > size_file)

        if flag:
            self.response(BAD_OFFSET)
            return

        size_buf = 500

        # Creamos el archivos que va a recibir el cliente
        try:
            f = open(path, 'rb')
        except OSError:
            self.response(INTERNAL_ERROR)
            return

        self.response(code_ok)
        # Mientras el tamaño del archivo sea más grande que el de nuestro
        # buffer vamos a ir mandando de a pedazos del tamaño de nuestro buffer,
        # después vamos a leer desde nuestro offset + buffer.
        f.seek(offset)
        while size > size_buf:
            file_slice = f.read(size_buf)
            self.output.append(str(len(file_slice)) + ' ' + file_slice + EOL)
            offset = offset + size_buf
            size = size - size_buf
        # Cuando el tamaño del archivo sea menor al del buffer,
        # lo mandamos directamente
        if (size > 0):
            file_slice = f.read(size)
            self.output.append(str(len(file_slice)) + ' ' + file_slice + EOL)
        self.output.append(str(code_ok) + ' ' + EOL)
        f.close()

    # Cerramos la conexión del socket

    def quit(self):
        """
        Habilita el cierre de la conexion
        """
        assert not self.remove
        self.response(code_ok)
        self.remove = True

    def send(self):
        """
        Envia datos al cliente
        """
        packet_len = self.s.send(self.output[0])
        if(packet_len < len(self.output[0])):
            self.output[0] = self.output[0][packet_len:]
        else:
            self.output.pop(0)

    def outputIsEmpty(self):
        """
        Verifica si el buffer de salida esta vacio
        """
        return self.output == []

    def closing(self):
        """
        Cierra definitivamente la conexion activa
        """
        self.s.close()
