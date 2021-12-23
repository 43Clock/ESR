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
    def __init__(self, connections, lock: RLock, network, alias, ottNetwork, tcpSocket, graph, connection,
                 client_address, streamingTo):
        Thread.__init__(self)
        self.connections = connections
        self.lock = lock
        self.network = network
        self.alias = alias
        self.ottNetwork = ottNetwork
        self.tcpSocket = tcpSocket
        self.graph = graph
        self.connection = connection
        self.client_address = client_address
        self.streamingTo = streamingTo

    def run(self):
        while True:
            received = self.connection.recv(MAX_SIZE).decode("UTF-8")
            self.lock.acquire()
            split = received.split("|")
            received = split[0]

            # Se nao for nenhuma mensagem que venha do servidor de streaming, atualiza as conexões com os nodos da
            # rede ott
            if received not in ["Stream","Stop","DisconnectStreaming"]:
                self.connections[self.get_alias_by_ip(self.client_address[0])] = self.connection

            if received == "Stream":
                self.createForwards(split[1])
                self.streamingTo.add(self.get_alias_by_ip(split[1]))
            elif received == "Stop":
                self.removeForwards(split[1])
            elif received == "Connect":
                self.updateNeighbours()
            elif received == "Disconnect":
                self.removeNeighbours()
            # Caso em que o servidor de streaming se disconecta
            elif received == "DisconnectStreaming":
                active_connection = [ele for ele in self.streamingTo]
                for ele in active_connection:
                    self.removeForwards(self.alias[ele][0])
                self.connection.close()
            self.lock.release()
            # Para de ouvir quando acaba a conecção
            if received == "Disconnect" or received == "DisconnectStreaming":
                self.connection.close()
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

    # Atualiza a lista dos vizinhos do nodo, enviando uma mensage, e caso alguma stream esteja a decorrer,
    # atualiza os forwards dos nodos para a nova configuração da rede (CASO DE ADICIONAR NODOS)
    def updateNeighbours(self):
        alias = self.get_alias_by_ip(self.client_address[0])
        # Caso inicial em que nada esta connectado
        if len(self.ottNetwork.keys()) == 0:
            self.ottNetwork[alias] = []
        # Caso em que existe so um vizinho conectado
        else:
            shortest = self.graph.getShortestPath(alias, "Servidor")
            node = None
            # Diz qual é o nomo mais proximo do Servidor no caminho entre o ip e o Servidor
            for ele in shortest:
                if ele in self.ottNetwork.keys():
                    node = ele
                    break
            self.ottNetwork[alias] = [node]
            self.ottNetwork[node].append(alias)
            neighbours = [item for item in self.ottNetwork[node]]
            for neigh in neighbours:
                if neigh != alias:
                    if alias in self.graph.getShortestPath(neigh, "Servidor"):
                        self.ottNetwork[neigh] = [alias if ele == node else ele for ele in self.ottNetwork[neigh]]
                        self.ottNetwork[node].remove(neigh)
                        self.ottNetwork[alias].append(neigh)
                        self.sendUpdate(neigh)
            self.sendUpdate(alias)
            self.sendUpdate(node)
        print(self.ottNetwork)
        # Atualizar forwards em caso de ja haver uma stream a correr
        for ele in self.streamingTo:
            if alias in self.graph.getShortestPath("Servidor", ele):
                self.updateForwardsOnAdd(ele,alias)

    # Atualiza a lista dos vizinhos do nodo, enviando uma mensage, e caso alguma stream esteja a decorrer,
    # atualiza os forwards dos nodos para a nova configuração da rede (CASO DE REMOVER NODOS)
    def removeNeighbours(self):
        alias = self.get_alias_by_ip(self.client_address[0])
        neighbours = [item for item in self.ottNetwork[alias]]
        for neigh in neighbours:
            path = self.graph.getShortestPath(neigh, "Servidor")
            # Caso em que o vizinho esta no caminho mais curto para o Servidor
            if alias in path:
                for ele in path[1:]:
                    if ele in self.ottNetwork.keys() and ele != alias:
                        self.ottNetwork[neigh].append(ele)
                        self.ottNetwork[ele].append(neigh)
                        break
            self.ottNetwork[neigh].remove(alias)

        # Da update a todos os vizinhos do nodo removido
        for neigh in neighbours:
            self.sendUpdate(neigh)

        self.ottNetwork.pop(alias, None)
        self.connections.pop(alias, None)
        print(self.ottNetwork)
        # Atualizar forwards em caso de ja haver uma stream a correr
        i = 0
        for ele in self.streamingTo:
            if alias in self.graph.getShortestPath("Servidor", ele):
                if i == 0:
                    self.updateForwardsOnRemove(ele,alias)
                    i += 1
                else:
                    self.createForwards(self.alias[ele][0])

    def sendUpdate(self, alias):
        # path = self.graph.getShortestPath(alias, "Bootstrap")
        # before = list(filter(None, [self.alias[i][0] if i != "Bootstrap" else "Bootstrap" if i in self.ottNetwork[alias] else None for i in path[1:]]))
        data = [self.alias[i][0] for i in self.ottNetwork[alias]]
        # Codifica para bytes com cada ip separado por ;
        message = bytes("neighbours|" + ";".join(data)+" ", "utf-8")
        self.connections[alias].sendall(message)

    def createForwards(self, ip):
        alias = self.get_alias_by_ip(ip)
        caminho = self.graph.getShortestPath("Servidor", alias)
        path = []
        for ele in caminho:
            if ele in self.ottNetwork.keys():
                path.append(ele)
        for i in range(0, len(path) - 1):
            origin = path[i]
            dest = path[i + 1]
            self.sendForwardUpdate(origin, dest)

    def sendForwardUpdate(self, origin, forward):
        message = bytes("forward|" + self.alias[forward][0]+" ", "utf-8")
        self.connections[origin].sendall(message)

    def removeForwards(self, ip):
        alias = self.get_alias_by_ip(ip)
        aux = self.graph.getShortestPath("Servidor", alias)
        removed_path = []
        for ele in aux:
            if ele in self.ottNetwork.keys():
                removed_path.append(ele)
        all_other_paths = []
        for ele in self.streamingTo:
            if ele != alias:
                all_other_paths.append(self.graph.getShortestPath("Servidor", ele))
        to_remove = []
        # Da flatten à all_other_paths
        for sublist in all_other_paths:
            for item in sublist:
                if item not in to_remove:
                    to_remove.append(item)
        n = 0
        for i in range(0, len(removed_path)):
            if removed_path[i] not in to_remove:
                n = i
                break
        if n == 0:
            n = 1
        for i in range(n, len(removed_path)):
            dest = removed_path[i]
            origin = removed_path[i - 1]
            self.removeForwardsUpdate(dest, origin)
        self.streamingTo.remove(alias)

    def removeForwardsUpdate(self, dest, origin):
        message = bytes("remove|" + self.alias[dest][0]+" ", "utf-8")
        self.connections[origin].sendall(message)

    def updateForwardsOnAdd(self,alias, new):
        caminho = self.graph.getShortestPath("Servidor", alias)
        path = []
        for ele in caminho:
            if ele in self.ottNetwork.keys():
                path.append(ele)
        path_bafore = []
        for ele in caminho:
            if ele == new:
                path.remove(ele)
                break
            path_bafore.append(ele)
            path.remove(ele)
        self.updateForwardsUpdate(path_bafore[len(path_bafore)-1],path[0],new)
        self.sendForwardUpdate(new,path[0])

    def updateForwardsOnRemove(self,alias, old):
        caminho = self.graph.getShortestPath("Servidor", alias)
        path = []
        for ele in caminho:
            if ele in self.ottNetwork.keys() or ele == old:
                path.append(ele)
        path_bafore = []
        for ele in caminho:
            if ele == old:
                path.remove(ele)
                break
            path_bafore.append(ele)
            path.remove(ele)
        self.updateForwardsUpdate(path_bafore[len(path_bafore)-1],old,path[0])

    def updateForwardsUpdate(self,alias,old,new):
        message = bytes("update|" + self.alias[old][0]+";"+self.alias[new][0]+" ", "utf-8")
        self.connections[alias].sendall(message)

class OttBootstrap:
    def __init__(self, file):
        self.connections = {}
        self.lock = RLock()
        self.network = {}
        self.alias = {}
        self.ottNetwork = {}
        self.tcpSocket = s.socket(s.AF_INET, s.SOCK_STREAM)
        self.read_config_file(file)
        self.graph = Graph(len(self.network.keys()))
        self.streamingTo = set()
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
            print("Ficheiro não existe")
            return

    def listenToTcp(self):
        server_address = ("", 8080)
        self.tcpSocket.bind(server_address)
        self.tcpSocket.listen(0)
        while True:
            connection, client_address = self.tcpSocket.accept()
            worker = TCPRequestHandler(self.connections, self.lock, self.network, self.alias, self.ottNetwork,
                                       self.tcpSocket, self.graph,
                                       connection, client_address, self.streamingTo)
            worker.start()


if __name__ == "__main__":
    try:
        bootstrap = OttBootstrap(sys.argv[1])
        bootstrap.listenToTcp()
    except IndexError:
        print("Ficheiro de configuração não recebido!")
