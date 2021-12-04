import socket
from threading import Thread
import socket as s
import sys
import re
from ottBootstrapper import OttBootstrap

MAX_SIZE = 4096


class Ott:
    def __init__(self, bootstrapper):
        self.bootstrapper = bootstrapper
        self.neighbours = []
        self.tcpSocket = s.socket(s.AF_INET, s.SOCK_STREAM)

    def recvall(self, n):
        # Helper function to recv n bytes or return None if EOF is hit
        data = bytearray()
        while len(data) < n:
            packet = self.tcpSocket.recv(n - len(data))
            if not packet:
                return None
            data.extend(packet)
        return data

    def sendConnectionMessage(self):
        server_address = (self.bootstrapper, 8080)
        self.tcpSocket.connect(server_address)
        message = b"Connect"
        self.tcpSocket.sendall(message)
        data = self.tcpSocket.recv(MAX_SIZE)
        print(data)
        # self.tcpSocket.close()


def check_if_ip(string):
    return re.match(r"((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)(\.|$)){4}", string) is not None


if __name__ == "__main__":
    try:
        if not check_if_ip(sys.argv[1]):
            ott = OttBootstrap(sys.argv[1])
            ott.listenToTcp()
        else:
            ott = Ott(sys.argv[1])
            ott.sendConnectionMessage()
    except IndexError:
        print("Not enough arguments")
