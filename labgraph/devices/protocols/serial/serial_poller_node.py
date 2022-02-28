#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

from labgraph.util.logger import get_logger
import serial


logger = get_logger(__name__)

class SERIALPollerNode():
    """
    Represents a node in the graph which polls data from PySerial.
    """
    
    def setup(self) -> None:
        self.serial = serial.Serial("/dev/pts/5")
        self.name = self.serial.name
    def cleanup(self) -> None:
        self.serial.close()
    def write(self) -> None:
        self.serial.write('hello'.encode('utf-8'))
    def read(self) -> bytes:
        return self.serial.readline()