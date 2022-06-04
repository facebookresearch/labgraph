import socket

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# connect, client connect
s.connect((socket.gethostname(), 1234))

# 1024 is our buffer, stream of data how big of a chunk of data we want to receive
full_msg = ''
while True:
    msg = s.recv(8)
    if(len(msg) <= 0):
        break
    full_msg += msg.decode("utf-8")
print(full_msg)
