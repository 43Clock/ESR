from ottBootstrapper import OttBootstrap
from ottNode import OttNode
import re
import sys


def check_if_ip(string):
    return re.match(r"((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)(\.|$)){4}", string) is not None


if __name__ == "__main__":
    try:
        if not check_if_ip(sys.argv[1]):
            ott = OttBootstrap(sys.argv[1])
            ott.listenToTcp()
        else:
            ott = OttNode(sys.argv[1])
            ott.sendConnectionMessage()
    except IndexError:
        print("Not enough arguments")
    finally:
        ott.tcpSocket.close()
