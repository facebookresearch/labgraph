#!/usr/bin/env python3
# Copyright (c) Meta Platforms, Inc. and affiliates.

import logging
import socket
import time
from typing import Dict, Sequence

import labgraph as lg

from messages_ft_ati import ForceTorchATIMessage


class ShutdownConfig(lg.Config):
    time_sleep_seconds: float = -1.0


class Shutdown(lg.Node):
    config: ShutdownConfig

    @lg.main
    def shutdown(self) -> None:
        if self.config.time_sleep_seconds > 0:
            time.sleep(self.config.time_sleep_seconds)
            raise lg.NormalTermination()


class ForceTorchATIConfig(lg.Config):
    """Configurations for Force Torch

    Args:
        poll_rate_hz (float): Poll Rate for FT Sensor,
            More details can be found in https://www.ati-ia.com/products/ft/ft_SystemInterfaces.aspx
        ATI_NET_FT_HOST_IP (str): Host IP for ATI NET FT
        ATI_NET_FT_IP (str): IP for ATI NET FT
        ATI_NET_FT_PORT (int): Port number for API NET FT
    """

    poll_rate_hz: float = 2000.0
    ATI_NET_FT_HOST_IP = "192.168.1.100"
    ATI_NET_FT_IP = "192.168.1.1"
    ATI_NET_FT_PORT = 49152
    bias: bool = False
    buffered: bool = True


class ForceTorchATISource(lg.Node):
    config: ForceTorchATIConfig
    OUTPUT = lg.Topic(ForceTorchATIMessage)

    ATI_NET_FT_HEADER = 0x1234
    ATI_NET_FT_CMD_STREAM = 0x02
    ATI_NET_FT_CMD_BUFFERED_STREAM = 0x03
    # Buffer size (1 to 40 integer)
    ATI_NET_FT_NUM_SAMPLES = 10
    ATI_NET_FT_RESPONSE_SIZE = 36

    def setup(self) -> None:
        self.poll_rate_hz = self.config.poll_rate_hz
        self.ATI_NET_FT_HOST_IP = self.config.ATI_NET_FT_HOST_IP
        self.ATI_NET_FT_IP = self.config.ATI_NET_FT_IP
        self.ATI_NET_FT_PORT = self.config.ATI_NET_FT_PORT
        self.bias = self.config.bias

        logging.info(
            "[{}] Setting up ForceSensorAti device at {}:{}".format(
                __class__.__name__, self.ATI_NET_FT_IP, self.ATI_NET_FT_PORT
            )
        )

        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._socket.settimeout(2)  # seconds
        self._socket.connect((self.ATI_NET_FT_IP, self.ATI_NET_FT_PORT))

        self._last_packet_time = time.time()
        self.shutdown = False

        # Data sampling rate (1 to 7000 Hz) and buffer size (1 to 40)
        # can be set at http://192.168.1.1/comm.htm
        # More details can be found at https://www.ati-ia.com/app_content/documents/9620-05-NET%20FT.pdf
        if self.config.buffered:
            self.ATI_NET_FT_CMD_CODE = self.ATI_NET_FT_CMD_BUFFERED_STREAM
        else:
            self.ATI_NET_FT_CMD_CODE = self.ATI_NET_FT_CMD_STREAM

        self.request = bytearray(8)
        self.request[0] = (self.ATI_NET_FT_HEADER & 0xFF00) >> 8
        self.request[1] = self.ATI_NET_FT_HEADER & 0xFF
        self.request[3] = self.ATI_NET_FT_CMD_CODE
        self.request[7] = self.ATI_NET_FT_NUM_SAMPLES

    def bias_resetting(self):
        logging.info(f"[{__class__.__name__}] Resetting bias")

        time.sleep(0.5)

        request = bytearray(8)
        request[0] = (self.ATI_NET_FT_HEADER & 0xFF00) >> 8
        request[1] = self.ATI_NET_FT_HEADER & 0xFF
        request[3] = self.ATI_NET_FT_CMD_BIAS

        self._socket.send(request)
        time.sleep(0.5)
        self.bias = False

    def unpack_force_torque_field(self, data: bytes, n: int) -> int:
        offset_to_values = 3
        field_length = 4
        return int.from_bytes(
            data[
                (offset_to_values + n)
                * field_length : (offset_to_values + n + 1)
                * field_length
            ],
            byteorder="big",
            signed=True,
        )

    @lg.publisher(OUTPUT)
    async def publish_ft_data(self) -> lg.AsyncPublisher:
        while not self.shutdown:
            if self.bias:
                self.bias_resetting()
                logging.info("[{}] NOT requesting data", __class__.__name__)
                return
            else:
                self._socket.send(self.request)

            try:
                data = self._socket.recv(self.ATI_NET_FT_RESPONSE_SIZE)
            except Exception:
                raise Exception(
                    f"[{__class__.__name__}] No ATI ForceSensor devices found, \
                    check ethernet connection and ensure the host PC IP address is set to \
                    {self.ATI_NET_FT_HOST_IP}"
                )

            if len(data) != self.ATI_NET_FT_RESPONSE_SIZE:
                raise Exception(
                    f"[{__class__.__name__}] Incomplete data packet received"
                )

            status = int.from_bytes(data[8:12], byteorder="big", signed=True)

            if status != 0:
                raise Exception(f"[{__class__.__name__}] Bad status received: {status}")

            yield self.OUTPUT, ForceTorchATIMessage(
                timestamp=time.time(),
                fx=self.unpack_force_torque_field(data, 0),
                fy=self.unpack_force_torque_field(data, 1),
                fz=self.unpack_force_torque_field(data, 2),
                tx=self.unpack_force_torque_field(data, 3),
                ty=self.unpack_force_torque_field(data, 4),
                tz=self.unpack_force_torque_field(data, 5),
            )

    def cleanup(self) -> None:
        self.shutdown = True


class ForceTorchATIGraph(lg.Graph):
    DEVICE: ForceTorchATISource
    # pyre-ignore[13] Shutdown is a Labgraph node
    SHUTDOWN: Shutdown

    FORCE_TORCH_RAW = lg.Topic(ForceTorchATIMessage)

    def process_modules(self) -> Sequence[lg.Module]:
        return (
            self.DEVICE,
            self.SHUTDOWN,
        )

    def connections(self) -> lg.Connections:
        return ((self.DEVICE.OUTPUT, self.FORCE_TORCH_RAW),)

    def logging(self) -> Dict[str, lg.Topic]:
        return {
            "ForceTorchMessage": self.DEVICE.OUTPUT,
        }


if __name__ == "__main__":
    lg.run(ForceTorchATIGraph)
