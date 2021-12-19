from threading import Thread
from ottBootstrapper import OttBootstrap
from ottNode import OttNode
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
                self.udpSocket.sendto(data,("127.0.0.1",25000))


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

    def removeForwards(self,fwds):
        print(fwds)
        if fwds in self.forward:
            self.forward.remove(fwds)
            print(self.forward)


if __name__ == "__main__":
    try:
        if not check_if_ip(sys.argv[1]):
            ott = OttBootstrap(sys.argv[1], Ott())
            ott.listenToTcp()
        else:
            ott = OttNode(sys.argv[1], Ott())
            ott.sendConnectionMessage()
    except IndexError:
        print("Not enough arguments")
