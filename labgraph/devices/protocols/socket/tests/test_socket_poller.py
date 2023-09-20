from socket_poller_node import SOCKETPollerNode

# Intial test to verify if the poller_node works
mySocketPoller = SOCKETPollerNode()
mySocketPoller.setup()

mySocketPoller.socket_monitor()
