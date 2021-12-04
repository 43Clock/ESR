import socket as sock
import sys

socket = sock.socket(sock.AF_INET,sock.SOCK_STREAM)

try:
    server_address = (sys.argv[1], 8080)
    print(f"Connecting to {server_address[0]} on port {server_address[1]}") 
    socket.connect(server_address)
    try:
        message = b'This is the message.  It will be repeated.'
        print(f'Sending {message}')
        socket.sendall(message)
        amount_received = 0
        amount_expected = len(message)
        while amount_received < amount_expected:
            data = socket.recv(16)
            amount_received += len(data)
            print('received {!r}'.format(data))
    finally:
        socket.close()
        
except IndexError:
    print("No IP given")