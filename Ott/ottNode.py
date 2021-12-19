import socket
from threading import Thread
import socket as s
import sys
import re
from ottBootstrapper import OttBootstrap
import atexit

MAX_SIZE = 4096

class OttNode:
    def __init__(self, bootstrapper, ott):
        self.ott = ott
        self.bootstrapper = bootstrapper
        self.neighbours = []
        self.forward = []
        self.tcpSocket = s.socket(s.AF_INET, s.SOCK_STREAM)
        atexit.register(self.exit_handler)

    def update(self, message):
        decoded = message.decode("UTF-8").split("|")
        if decoded[0] == "neighbours":
            self.neighbours = decoded[1].split(";")
        elif decoded[0] == "forward":
            self.ott.addForwards(decoded[1])
        elif decoded[0] == "remove":
            self.ott.removeForwards(decoded[1])

        print("Neighbours: ", self.neighbours)
        print("Forward: ", self.ott.forward)

    def sendConnectionMessage(self):
        server_address = (self.bootstrapper, 8080)
        self.tcpSocket.connect(server_address)
        message = b"Connect"
        self.tcpSocket.sendall(message)
        # Descodifica e depois fica a ouvir sempre
        while True:
            update = self.tcpSocket.recv(MAX_SIZE)
            self.update(update)
        # self.tcpSocket.close()

    def exit_handler(self):
        print("Shuting down, message sent")
        self.tcpSocket.sendall(b"Disconnect")
        self.tcpSocket.close()
