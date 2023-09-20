from http import client
import socket

# AF: Adress family, IPv4??
# s: socket object
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((socket.gethostname(), 1234))  # Tie
s.listen(5)

while True:
    clientsocket, address = s.accept()
    print(f"Connection from {address} has been established!")
    # client socket is our local version of the client's socket,
    # so we send information to the client
    clientsocket.send(bytes("Welcome to the server!", "utf-8"))
    clientsocket.close()
