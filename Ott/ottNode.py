import socket
from threading import Thread
import socket as s
import sys
import re
from ottBootstrapper import OttBootstrap
import atexit

MAX_SIZE = 4096


class OttNode:
    def __init__(self, bootstrapper):
        self.bootstrapper = bootstrapper
        self.neighbours = []
        self.forward = []
        self.tcpSocket = s.socket(s.AF_INET, s.SOCK_STREAM)
        atexit.register(self.exit_handler)

    def updateNeighbours(self, message):
        decoded = message.decode("UTF-8").split("|")
        self.neighbours = decoded[0].split(";")
        self.forward = list(filter(lambda x: x != "", decoded[1].split(";")))
        print("Neighbours: ", self.neighbours)
        print("Forward: ", self.forward)

    def sendConnectionMessage(self):
        server_address = (self.bootstrapper, 8080)
        self.tcpSocket.connect(server_address)
        message = b"Connect"
        self.tcpSocket.sendall(message)
        # Descodifica e depois fica a ouvir sempre
        while True:
            update = self.tcpSocket.recv(MAX_SIZE)
            self.updateNeighbours(update)
        # self.tcpSocket.close()

    def exit_handler(self):
        print("Shuting down, message sent")
        self.tcpSocket.sendall(b"Disconnect")
        self.tcpSocket.close()
