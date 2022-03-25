#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserve

import labgraph as lg
from typing import Tuple
from labgraph.websockets.ws_server.ws_api_node_server import (
    WSAPIServerConfig,
    WSAPIServerNode
)
from .serializer_node import SerializerConfig, Serializer
from ..aliases.aliases import SerializedGraph
from .enums.enums import ENUMS

# Add additional nodes
from ....graphviz_support.graphviz_support.tests.demo_graph.noise_generator import NoiseGenerator, NoiseGeneratorConfig
from ....graphviz_support.graphviz_support.tests.demo_graph.amplifier import Amplifier, AmplifierConfig
from ....graphviz_support.graphviz_support.tests.demo_graph.attenuator import Attenuator, AttenuatorConfig
from ....graphviz_support.graphviz_support.tests.demo_graph.rolling_averager import RollingAverager, RollingConfig

# Needed test configurations
NUM_FEATURES = 100
WINDOW = 2.0
REFRESH_RATE = 2.0
OUT_IN_RATIO = 1.2
ATTENUATION = 5.0

APP_ID = 'LABGRAPH.MONITOR'
WS_SERVER = ENUMS.WS_SERVER
STREAM = ENUMS.STREAM
DEFAULT_IP = WS_SERVER.DEFAULT_IP
DEFAULT_PORT = WS_SERVER.DEFAULT_PORT
DEFAULT_API_VERSION = WS_SERVER.DEFAULT_API_VERSION
SAMPLE_RATE = 5

class WSSenderNode(lg.Graph):
        SERIALIZER: Serializer
        WS_SERVER_NODE: WSAPIServerNode

        NOISE_GENERATOR: NoiseGenerator
        ROLLING_AVERAGER: RollingAverager
        AMPLIFIER: Amplifier
        ATTENUATOR: Attenuator

        def setup_data(self, data) -> None:
            self.data = data

        def setup(self) -> None:
            self.WS_SERVER_NODE.configure(
                WSAPIServerConfig(
                    app_id=APP_ID,
                    ip=WS_SERVER.DEFAULT_IP,
                    port=ENUMS.WS_SERVER.DEFAULT_PORT,
                    api_version=ENUMS.WS_SERVER.DEFAULT_API_VERSION,
                    num_messages=-1,
                    enums=ENUMS(),
                    sample_rate=SAMPLE_RATE,
                )
            )
            self.SERIALIZER.configure(
                SerializerConfig(
                    data=self.data,
                    sample_rate=SAMPLE_RATE,
                    stream_name=STREAM.LABGRAPH_MONITOR,
                    stream_id=STREAM.LABGRAPH_MONITOR_ID
                )
            )
            self.NOISE_GENERATOR.configure(
            NoiseGeneratorConfig(
                sample_rate=float(SAMPLE_RATE),
                num_features=NUM_FEATURES
                )
            )

            self.ROLLING_AVERAGER.configure(
                RollingConfig(window=WINDOW)
            )

            self.AMPLIFIER.configure(
                AmplifierConfig(out_in_ratio=OUT_IN_RATIO)
            )

            self.ATTENUATOR.configure(
                AttenuatorConfig(attenuation=ATTENUATION)
            )

        def connections(self) -> lg.Connections:
            return (
                (self.NOISE_GENERATOR.OUTPUT, self.ROLLING_AVERAGER.INPUT),
                (self.NOISE_GENERATOR.OUTPUT, self.AMPLIFIER.INPUT),
                (self.NOISE_GENERATOR.OUTPUT, self.ATTENUATOR.INPUT),
                (self.NOISE_GENERATOR.OUTPUT, self.SERIALIZER.INPUT_1),
                (self.ROLLING_AVERAGER.OUTPUT, self.SERIALIZER.INPUT_2),
                (self.AMPLIFIER.OUTPUT, self.SERIALIZER.INPUT_3),
                (self.ATTENUATOR.OUTPUT, self.SERIALIZER.INPUT_4),
                (self.SERIALIZER.TOPIC, self.WS_SERVER_NODE.topic),
            )

        def process_modules(self) -> Tuple[lg.Module, ...]:
            return (
                self.NOISE_GENERATOR,
                self.ROLLING_AVERAGER,
                self.AMPLIFIER,
                self.ATTENUATOR,
                self.SERIALIZER, 
                self.WS_SERVER_NODE,
            )

def run_server(data: SerializedGraph) -> None:
    """
    A function that creates a Websocket server graph.
    The server graph streams the lagraph topology to the clients
    """
    WS = WSSenderNode()
    WS.setup_data(data)

    runner = lg.ParallelRunner(graph=WS)
    runner.run()
