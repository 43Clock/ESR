import socket
from threading import Thread, RLock
import socket as s
import sys
import re
import json
from graphs import Graph
import time

MAX_SIZE = 4096


class TCPRequestHandler(Thread):
    def __init__(self, ott, connections, lock: RLock, network, alias, ottNetwork, tcpSocket, graph, connection,
                 client_address):
        Thread.__init__(self)
        self.ott = ott
        self.connections = connections
        self.lock = lock
        self.network = network
        self.alias = alias
        self.ottNetwork = ottNetwork
        self.tcpSocket = tcpSocket
        self.graph = graph
        self.connection = connection
        self.client_address = client_address

    def run(self):
        while True:
            received = self.connection.recv(MAX_SIZE).decode("UTF-8")
            self.lock.acquire()
            self.connections[self.get_alias_by_ip(self.client_address[0])] = self.connection
            if received == "Teste":
                self.createForwards()
            else:
                self.calculateNeighbours(received)
            self.lock.release()
            # Para de ouvir quando acaba a conecção
            if received == "Disconnect":
                break

    # Retorna o numero de vizinhos de um ip que se encontram na rede ott
    def check_how_many_neighbour(self):
        r = 0
        for neighbour in self.network[self.client_address[0]]:
            if neighbour in self.ottNetwork.keys():
                r += 1
        return r

    # Retorna todos os vizinhos na rede ott de um certo ip
    def neighbours_in_ott(self):
        neigh = []
        for neighbour in self.network[self.client_address[0]]:
            if neighbour in self.ottNetwork.keys():
                neigh.append(neighbour)
        return neigh

    def get_alias_by_ip(self, ip):
        for key in self.alias.keys():
            for item in self.alias[key]:
                if item == ip:
                    return key

    def calculateNeighbours(self, message):
        alias = self.get_alias_by_ip(self.client_address[0])
        if message == "Connect":
            # Caso inicial em que nada esta connectado
            if len(self.ottNetwork.keys()) == 0:
                self.ottNetwork[alias] = ["Bootstrap"]
                self.ottNetwork["Bootstrap"] = [alias]
                self.sendUpdate(alias)
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
                            self.sendUpdate(neigh)
                self.sendUpdate(alias)
                # So manda para o node caso este não seja o bootstrap
                if node != "Bootstrap":
                    self.sendUpdate(node)
        #@TODO VERIFICAR MELHOR ISTO
        elif message == "Disconnect" and alias in self.ottNetwork.keys():
            neighbours = [item for item in self.ottNetwork[alias]]
            for neigh in neighbours:
                path = self.graph.getShortestPath(neigh, "Bootstrap")
                # Caso em que o vizinho esta no caminho mais curto para o Bootstrap
                if alias in path:
                    for ele in path[1:]:
                        if ele in self.ottNetwork.keys() and ele != alias:
                            self.ottNetwork[neigh].append(ele)
                            self.ottNetwork[ele].append(neigh)
                            break
                
                self.ottNetwork[neigh].remove(alias)
            
            # Da update a todos os vizinhos do nodo removido    
            for neigh in neighbours:
                if neigh != "Bootstrap":
                        self.sendUpdate(neigh)
                              
            self.ottNetwork.pop(alias, None)
            self.connections.pop(alias, None)
        print(self.ottNetwork)

    def sendUpdate(self, alias):
        #path = self.graph.getShortestPath(alias, "Bootstrap")
        #before = list(filter(None, [self.alias[i][0] if i != "Bootstrap" else "Bootstrap" if i in self.ottNetwork[alias] else None for i in path[1:]]))
        data = [self.alias[i][0] if i != "Bootstrap" else "Bootstrap" for i in self.ottNetwork[alias]]
        # Codifica para bytes com cada ip separado por ;
        message = bytes("neighbours|"+";".join(data),"utf-8")
        self.connections[alias].sendall(message)


    def createForwards(self):
        alias = self.get_alias_by_ip(self.client_address[0])
        caminho = self.graph.getShortestPath("Bootstrap",alias)
        path = []
        for ele in caminho:
            if ele in self.ottNetwork.keys():
                if ele == "Bootstrap":
                    path.append(ele)
                else:
                    path.append(self.alias[ele][0])
        print(path)  
        for i in range(0,len(path)-1):
            origin = path[i]
            dest = path[i+1]
            if origin == "Bootstrap":
                self.ott.updateForwards(dest)
            else:
                self.sendForwardUpdate(origin,dest)
        time.sleep(1)
        self.ott.sendHello()
                
    def sendForwardUpdate(self, ip, forward):
        message = bytes("forward|"+forward,"utf-8")
        self.connections[self.get_alias_by_ip(ip)].sendall(message)
        
        
class OttBootstrap:
    def __init__(self, file, ott):
        self.ott = ott
        self.connections = {}
        self.lock = RLock()
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

    def listenToTcp(self):
        server_address = ("", 8080)
        self.tcpSocket.bind(server_address)
        self.tcpSocket.listen(0)
        while True:
            connection, client_address = self.tcpSocket.accept()
            print(client_address)
            worker = TCPRequestHandler(self.ott, self.connections, self.lock, self.network, self.alias, self.ottNetwork,
                                       self.tcpSocket, self.graph,
                                       connection, client_address)
            worker.start()
            # try:
            #     print(f"Connection from {client_address}")
            #     data = connection.recv(MAX_SIZE)
            #     self.calculateNeighbours(client_address[0])
            #     connection.sendall(b"AIUWGDUIWGAIUD")
            # finally:
            #     connection.close()
