import atexit
from threading import Thread
import re
import sys
import socket
from queue import Queue


def check_if_ip(string):
    return re.match(r"((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)(\.|$)){4}", string) is not None


class UDPListener(Thread):
    def __init__(self, udpSocket: socket.socket, queue: Queue):
        Thread.__init__(self)
        self.udpSocket = udpSocket
        self.queue = queue

    def run(self):
        while True:
            data = self.udpSocket.recvfrom(20480)
            self.queue.put(data[0])


class UDPSender(Thread):

    def __init__(self, udpSocket, queue, forward):
        Thread.__init__(self)
        self.udpSocket = udpSocket
        self.queue = queue
        self.forward = forward

    def run(self):
        while True:
            data = self.queue.get()
            if len(self.forward) > 0:
                for ele in self.forward:
                    self.udpSocket.sendto(data, (ele, 8888))
            else:
                self.udpSocket.sendto(data, ("127.0.0.1", 25000))


class Ott():

    def __init__(self):
        self.udpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udpSocket.bind(("", 8888))
        self.forward = []
        self.queue = Queue(maxsize=0)
        listener = UDPListener(self.udpSocket, self.queue)
        listener.start()
        sender = UDPSender(self.udpSocket, self.queue, self.forward)
        sender.start()

    def addForwards(self, fwds):
        if fwds not in self.forward:
            self.forward.append(fwds)
        print("Forwards: ", self.forward)

    def removeForwards(self, fwds):
        if fwds in self.forward:
            self.forward.remove(fwds)
        print("Forwards: ", self.forward)

    def updateForwards(self,update):
        split = update.split(";")
        if split[0] in self.forward:
            self.forward.remove(split[0])
        if not split[1] in self.forward:
            self.forward.append(split[1])
        print("Forwards: ", self.forward)

class OttNode:
    def __init__(self, bootstrapper):
        self.ott = Ott()
        self.bootstrapper = bootstrapper
        self.neighbours = []
        self.forward = []
        self.tcpSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        atexit.register(self.exit_handler)

    def update(self, message):
        all_updates = message.decode("UTF-8").split(" ")
        for msg in all_updates:
            decoded = msg.split("|")
            if decoded[0] == "neighbours":
                self.neighbours = decoded[1].split(";")
            elif decoded[0] == "forward":
                self.ott.addForwards(decoded[1])
            elif decoded[0] == "remove":
                self.ott.removeForwards(decoded[1])
            elif decoded[0] == "update":
                self.ott.updateForwards(decoded[1])

        print("Neighbours: ", self.neighbours)

    def sendConnectionMessage(self):
        server_address = (self.bootstrapper, 8080)
        self.tcpSocket.connect(server_address)
        message = b"Connect"
        self.tcpSocket.sendall(message)
        # Descodifica e depois fica a ouvir sempre
        while True:
            update = self.tcpSocket.recv(4096)
            self.update(update)
        # self.tcpSocket.close()

    def exit_handler(self):
        print("Shuting down, message sent")
        self.tcpSocket.sendall(b"Disconnect")
        self.tcpSocket.close()


if __name__ == "__main__":
    try:
        if check_if_ip(sys.argv[1]):
            ott = OttNode(sys.argv[1])
            ott.sendConnectionMessage()
        else:
            print("IP Inválido!")
    except IndexError:
        print("Not enough arguments")
