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
        self.network = {}
        self.alias = {}
        self.ottNetwork = {}
        self.tcpSocket = s.socket(s.AF_INET, s.SOCK_STREAM)
        self.read_config_file(file)
        self.graph = Graph(len(self.network.keys()))
        for key in self.network.keys():
            for ele in self.network[key]:
                self.graph.add_edge(key, ele)

    def read_config_file(self, file):
        try:
            with open(file) as f:
                data = json.load(f)
                self.network = data["connections"]
                self.alias = data["alias"]
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

    def get_alias_by_ip(self, ip):
        for key in self.alias.keys():
            for item in self.alias[key]:
                if item == ip:
                    return key

    def calculateNeighbours(self, ip):

        # Caso inicial em que nada esta connectado
        alias = self.get_alias_by_ip(ip)
        if len(self.ottNetwork.keys()) == 0:
            #self.tcpSocket.send(b"Bootstrap")
            self.ottNetwork[alias] = ["Bootstrap"]
            self.ottNetwork["Bootstrap"] = [alias]
        # Caso em que existe so um vizinho conectado
        else:
            shortest = self.graph.getShortestPath(alias, "Bootstrap")
            node = None
            # Diz qual é o nomo mais proximo do bootstrap no caminho entre o ip e o bootstrap
            for ele in shortest:
                if ele in self.ottNetwork.keys():
                    node = ele
                    break
            self.ottNetwork[alias] = [node]
            self.ottNetwork[node].append(alias)
            neighbours = [item for item in self.ottNetwork[node]]
            for neigh in neighbours:
                if neigh != alias:
                    if alias in self.graph.getShortestPath(neigh, "Bootstrap"):
                        self.ottNetwork[neigh] = [alias if ele == node else ele for ele in self.ottNetwork[neigh]]
                        self.ottNetwork[node].remove(neigh)
                        self.ottNetwork[alias].append(neigh)
                        #@TODO MANDAR MSG AO NEIGH
            #@TODO MANDAR MSG AOS outros
        print(self.ottNetwork)


    def listenToTcp(self):
        server_address = ("", 8080)
        self.tcpSocket.bind(server_address)
        self.tcpSocket.listen(0)
        while True:
            connection, client_address = self.tcpSocket.accept()
            try:
                print(f"Connection from {client_address}")
                data = connection.recv(MAX_SIZE)
                self.calculateNeighbours(client_address[0])
                connection.sendall(b"AIUWGDUIWGAIUD")
            finally:
                connection.close()
