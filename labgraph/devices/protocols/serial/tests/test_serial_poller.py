from labgraph.devices.protocols.serial.serial_poller_node import SERIALPollerNode

serial_poller = SERIALPollerNode()

serial_poller.setup()

serial_poller.write()

serial_poller.read()

serial_poller.cleanup()