import socket as sock
import sys

arguments = sys.argv

socket = sock.socket(sock.AF_INET,sock.SOCK_STREAM)

server_address = ("", 8080)
print(f"Starting up on {server_address[0]}, on port {server_address[1]}")
socket.bind(server_address)

socket.listen(1)

while True:
    connection, client_address = socket.accept()
    try:
        print(f"Connection from {client_address}")
        while True:
            data = connection.recv(16)
            print(f"Received {data}")
            if data:
                connection.sendall(data)
            else:
                break
    finally:
        connection.close()
