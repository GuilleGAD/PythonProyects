# encoding: utf-8
# Copyright 2014 Carlos Bederián
# $Id: connection.py 455 2011-05-01 00:32:09Z carlos $

import socket
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
        self.connected = False
        self.address = ''
        self.command = ''
        # FALTA: Inicializar atributos de Connection
        pass

    ##Recibimos datos (un string) desde el cliente
    #y los ponemos en una cola de comandos; leemos hasta un EOL
    #y tomamos el comando, dejando el resto del string disponible
    #para seguir concatenandole cosas. Usamos la función 'partition'
    #porque es muy útil y fácil para cumplir el objetivo.
    def recive(self):
        assert(self.connected)

        while not EOL in self.datos and self.connected:
            self.datos += self.s.recv(4096)
            if self.datos=='':
                self.quit()
        if(self.connected):
            self.command, sep, rest = self.datos.partition(EOL)
            self.datos = rest
        return self.command

    #Parseamos los datos recibidos del cliente y ejecutamos según corresponda.
    #Llamamos a cada función en el parser.

    def handle(self, command):
        """
        Atiende eventos de la conexión hasta que termina.
        """
        # FALTA: Manejar recepciones y envíos hasta desconexión
        command_list = command.split(' ')
        command_list_len = len(command_list)
        if not '\n' in command:
            if command_list[0] == "get_file_listing":
                if command_list_len == 1:
                    self.get_file_listing()
                else:
                    if self.connected:
                        self.s.send(response(INVALID_ARGUMENTS))
            elif command_list[0] == "get_metadata":
                if command_list_len == 2:
                    self.get_metadata(command_list[1])
                else:
                    if self.connected:
                        self.s.send(response(INVALID_ARGUMENTS))
            elif command_list[0] == "get_slice":
                if command_list_len == 4:
                    self.get_slice(command_list[1],
                                   command_list[2], command_list[3])
                else:
                    if self.connected:
                        self.s.send(response(INVALID_ARGUMENTS))
            elif command_list[0] == "quit":
                if command_list_len == 1:
                    self.quit()
                else:
                    if self.connected:
                        self.s.send(response(INVALID_ARGUMENTS))
            else:
                if self.connected:
                    self.s.send(response(INVALID_COMMAND))
        else:
            if self.connected:
                self.s.send(response(BAD_EOL))

    def get_file_listing(self):
        import ipdb; ipdb.set_trace()
        try:
            listdir = os.listdir(self.directory)
        except OSError:
            if self.connected:
                self.s.send(error_messages[INTERNAL_ERROR] + ' ' + EOL)
            return
        for i in range(len(listdir)):
            listdir[i] += EOL
        if self.connected:
            self.s.send(response(CODE_OK)+''.join(listdir)+EOL)

    def get_metadata(self, filename):
        ### Convertimos el string "filename" en un conjunto y nos fijamos
        #si pertenece al tipo alphanum. El nombre original no se modifica.
        #print 'filename:' + filename
        assert (filename != "")
        setfilename = set(filename)
        is_alpha = setfilename.issubset(alphaset)
        #Si pertenece al conjunto nos fijamos que exista
        #y respondemos con '0 Ok'
        if is_alpha:
            try:
                path = os.path.join(self.directory, filename)
                b = os.path.exists(path)
            except OSError:
                if self.connected:
                    self.s.send(response(INTERNAL_ERROR))
                return
            if b:
                if self.connected:
                    self.s.send(response(CODE_OK))
                #print os.path.getsize(path)
                    self.s.send(str(os.path.getsize(path)) + EOL)
            else:
                if self.connected:
                    self.s.send(response(FILE_NOT_FOUND))
        else:
            if self.connected:
                self.s.send(response(INVALID_ARGUMENTS))

    def get_slice(self, filename, str_offset, str_size):
        assert (filename[0] != '/' or filename != "" or str_size != "")
        ## Primero chequeamos que los ultimos dos parametros de la funcion sean
        # del tipo numero y luego verificamos si el archivo esta disponible
        try:
            path = os.path.join(self.directory, filename)
            file_exists = os.path.exists(path)
        except OSError:
            if self.connected:
                self.s.send(response(INTERNAL_ERROR))
            return

        if not file_exists:
            if self.connected:
                self.s.send(response(FILE_NOT_FOUND))
            return

        if not (str_offset.isdigit() and str_size.isdigit()):
            if self.connected:
                self.s.send(response(INVALID_ARGUMENTS))
            return

        try:
            size_file = os.path.getsize(path)
        except OSError:
            if self.connected:
                self.s.send(response(INTERNAL_ERROR))
            return
        size = int(str_size)
        offset = int(str_offset)
        b = (offset + size > size_file) or (offset > size_file)

        if b:
            if self.connected:
                self.s.send(response(BAD_OFFSET))
            return

        size_buf = 500

        #Creamos el archivos que va a recibir el cliente
        try:
            f = open(path, 'rb')
        except OSError:
            if self.connected:
                self.s.send(response(INTERNAL_ERROR))
            return
        if self.connected:
            self.s.send(response(CODE_OK))
        ##Mientras el tamaño del archivo sea más grande que el de nuestro
        #buffer vamos a ir mandando de a pedazos del tamaño de nuestro buffer,
        #después vamos a leer desde nuestro offset + buffer.
        f.seek(offset)
        while size > size_buf:
            file_slice = f.read(size_buf)
            if self.connected:
                self.s.send(str(len(file_slice)) + ' ' + file_slice + EOL)
            offset = offset + size_buf
            size = size - size_buf
        #Cuando el tamaño del archivo sea menor al del buffer,
        #lo mandamos directamente
        if (size > 0):
            file_slice = f.read(size)
            if self.connected:
                self.s.send(str(len(file_slice)) + ' ' + file_slice + EOL)
        if self.connected:
            self.s.send('0 ' + EOL)
        f.close()

    #Cerramos la conexión del socket

    def quit(self):
        if self.connected:
            self.s.send(response(CODE_OK))
        self.s.close()
        self.connected = False
