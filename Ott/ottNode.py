import socket
from threading import Thread
import socket as s
import sys
import re
from ottBootstrapper import OttBootstrap

MAX_SIZE = 4096


class OttNode:
    def __init__(self, bootstrapper):
        self.bootstrapper = bootstrapper
        self.neighbours = []
        self.tcpSocket = s.socket(s.AF_INET, s.SOCK_STREAM)

    def updateNeighbours(self, message):
        self.neighbours = message.decode("UTF-8").split(";")

    def sendConnectionMessage(self):
        server_address = (self.bootstrapper, 8080)
        self.tcpSocket.connect(server_address)
        message = b"Connect"
        self.tcpSocket.sendall(message)
        # Descodifica e depois fica a ouvir sempre
        while True:
            update = self.tcpSocket.recv(MAX_SIZE)
            self.updateNeighbours(update)
            print(self.neighbours)
        # self.tcpSocket.close()
