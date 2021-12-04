import socket
from threading import Thread
import socket as s
import sys
import re
import json
from graphs import Graph

MAX_SIZE = 4096


class OttBootstrap:
    def __init__(self, file):
        self.graph = Graph()
        self.network = {}
        self.ottNetwork = {}
        self.tcpSocket = s.socket(s.AF_INET, s.SOCK_STREAM)
        self.read_config_file(file)
        for key in self.network.keys():
            for ele in self.network[key]:
                self.graph.add_edge(key, ele)

    def read_config_file(self, file):
        try:
            with open(file) as f:
                self.network = json.load(f)
        except FileNotFoundError:
            return

    # Retorna o numero de vizinhos de um ip que se encontram na rede ott
    def check_how_many_neighbour(self, ip):
        r = 0
        for neighbour in self.network[ip]:
            if neighbour in self.ottNetwork.keys():
                r += 1
        return r

    # Retorna todos os vizinhos na rede ott de um certo ip
    def neighbours_in_ott(self, ip):
        neigh = []
        for neighbour in self.network[ip]:
            if neighbour in self.ottNetwork.keys():
                neigh.append(neighbour)
        return neigh

    def calculateNeighbours(self, ip):
        # Caso inicial em que nada esta connectado
        if len(self.ottNetwork.keys()) == 0:
            self.tcpSocket.send(b"Bootstrap")
            self.ottNetwork[ip] = ["Bootstrap"]
            self.ottNetwork["Bootstrap"] = [ip]
        # Caso em que existe so um vizinho conectado
        elif self.check_how_many_neighbour(ip) == 1:
            neighbour = self.neighbours_in_ott(ip)[0]
            self.ottNetwork[ip] = [neighbour]
            self.ottNetwork[neighbour].append(ip)

    def listenToTcp(self):
        server_address = ("", 8080)
        self.tcpSocket.bind(server_address)
        self.tcpSocket.listen(0)
        while True:
            connection, client_address = self.tcpSocket.accept()
            try:
                print(f"Connection from {client_address}")
                while True:
                    data = connection.recv(MAX_SIZE)
                    self.calculateNeighbours(client_address)
                    if data:
                        connection.sendall(b"AIUWGDUIWGAIUD")
                    else:
                        break
            finally:
                connection.close()
