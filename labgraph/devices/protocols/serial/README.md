The way I'm able to test it right now is the following:

First, I make sure to create a virtual port like `pty`

```python
import os
import pty
import serial

parent, child = pty.openpty() # ex. parent is 13, child is 14
s_name = os.ttyname(child) #  ex. `/dev/pts/5`

ser = serial.Serial(s_name) # opens a serial port
ser.write("wow".encode("utf-8")) # writes b'wow' to the port
os.read(parent, 1000) # reads b'wow' from the port
```

Having setup the `/dev/pts/5` port, I can run `python -m labgraph.devices.protocols.serial.tests.test_serial_poller`.

It will write `'hello'.encode('utf-8')` to the terminal. So having run `os.read(parent, 1000)` again, I get `b'wowhello'`.s