from socket_sender_node import SOCKETSenderNode

# Initial test to verify if the poller_node works
mySocketSender = SOCKETSenderNode()
mySocketSender.setup()

mySocketSender.socket_monitor()
