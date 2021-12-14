import sys
from tkinter import Tk
from ClienteGUI import ClienteGUI
import re


def check_if_ip(string):
    return re.match(r"((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)(\.|$)){4}", string) is not None


if __name__ == "__main__":
    try:
        addr = '127.0.0.1'
        port_udp = 25000
        port_tcp = 9999
        server_ip = sys.argv[1]
        if check_if_ip(server_ip):
            root = Tk()

            # Create a new client
            app = ClienteGUI(root, addr, port_udp, server_ip, port_tcp)
            app.master.title("Cliente Exemplo")
            root.mainloop()
    except IndexError:
        print("No Ip given\n")


