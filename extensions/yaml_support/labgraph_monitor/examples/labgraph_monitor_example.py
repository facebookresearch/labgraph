#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

from wsgiref.simple_server import demo_app
import labgraph as lg
from typing import Dict, Tuple

# Make the imports work when running from LabGraph root directory
import sys
sys.path.append("./")

# LabGraph WebSockets Components
from labgraph.websockets.ws_server.ws_api_node_server import (
    WSAPIServerConfig,
    WSAPIServerNode,
)

# LabGraph Monitor Components
from extensions.yaml_support.labgraph_monitor.server.enums.enums import ENUMS
from extensions.yaml_support.labgraph_monitor.aliases.aliases import SerializedGraph
from extensions.yaml_support.labgraph_monitor.server.serializer_node import SerializerConfig, Serializer
from extensions.yaml_support.labgraph_monitor.generate_lg_monitor.generate_lg_monitor import set_graph_topology

# Graph Components
from extensions.graphviz_support.graphviz_support.tests.demo_graph.noise_generator import NoiseGeneratorConfig, NoiseGenerator
from extensions.graphviz_support.graphviz_support.tests.demo_graph.amplifier import AmplifierConfig, Amplifier
from extensions.graphviz_support.graphviz_support.tests.demo_graph.attenuator import AttenuatorConfig, Attenuator
from extensions.graphviz_support.graphviz_support.tests.demo_graph.rolling_averager import RollingConfig, RollingAverager

# LabGraph WebSockets Configurations
APP_ID = 'LABGRAPH.MONITOR'
WS_SERVER = ENUMS.WS_SERVER
STREAM = ENUMS.STREAM
DEFAULT_IP = WS_SERVER.DEFAULT_IP
DEFAULT_PORT = WS_SERVER.DEFAULT_PORT
DEFAULT_API_VERSION = WS_SERVER.DEFAULT_API_VERSION
SAMPLE_RATE = 5

# Graph Configurations
NUM_FEATURES = 100
WINDOW = 2.0
REFRESH_RATE = 2.0
OUT_IN_RATIO = 1.2
ATTENUATION = 5.0

class Demo(lg.Graph):
    # LabGraph WebSockets Component
    WS_SERVER_NODE: WSAPIServerNode

    # LabGraph Monitor Component
    SERIALIZER: Serializer

    # Graph Components
    NOISE_GENERATOR: NoiseGenerator
    ROLLING_AVERAGER: RollingAverager
    AMPLIFIER: Amplifier
    ATTENUATOR: Attenuator

    # Used when running `generate_labgraph_monitor(graph)`
    def set_topology(self, topology: SerializedGraph, sub_pub_map: Dict) -> None:
        self._topology = topology
        self._sub_pub_match = sub_pub_map

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
                data=self._topology,
                sub_pub_match=self._sub_pub_match,
                sample_rate=SAMPLE_RATE,
                stream_name=STREAM.LABGRAPH_MONITOR,
                stream_id=STREAM.LABGRAPH_MONITOR_ID,
            )
        )
        self.NOISE_GENERATOR.configure(
            NoiseGeneratorConfig(
                sample_rate=float(SAMPLE_RATE),
                num_features=NUM_FEATURES,
            )
        )
        self.ROLLING_AVERAGER.configure(
            RollingConfig(
                window=WINDOW,
            )
        )
        self.AMPLIFIER.configure(
            AmplifierConfig(
                out_in_ratio=OUT_IN_RATIO,
            )
        )
        self.ATTENUATOR.configure(
            AttenuatorConfig(
                attenuation=ATTENUATION,
            )
        )            
        
    def returnConnect(self):
        return (
            (self.NOISE_GENERATOR.NOISE_GENERATOR_OUTPUT, self.ROLLING_AVERAGER.ROLLING_AVERAGER_INPUT),
            (self.NOISE_GENERATOR.NOISE_GENERATOR_OUTPUT, self.AMPLIFIER.AMPLIFIER_INPUT),
            (self.NOISE_GENERATOR.NOISE_GENERATOR_OUTPUT, self.ATTENUATOR.ATTENUATOR_INPUT),
            (self.NOISE_GENERATOR.NOISE_GENERATOR_OUTPUT, self.SERIALIZER.SERIALIZER_INPUT_1),
            (self.ROLLING_AVERAGER.ROLLING_AVERAGER_OUTPUT, self.SERIALIZER.SERIALIZER_INPUT_2),
            (self.AMPLIFIER.AMPLIFIER_OUTPUT, self.SERIALIZER.SERIALIZER_INPUT_3),
            (self.ATTENUATOR.ATTENUATOR_OUTPUT, self.SERIALIZER.SERIALIZER_INPUT_4),
            (self.SERIALIZER.SERIALIZER_OUTPUT, self.WS_SERVER_NODE.topic),
        )

    def connections(self) -> lg.Connections:
        
        return self.returnConnect()

    def process_modules(self) -> Tuple[lg.Module, ...]:
        return (
            self.NOISE_GENERATOR,
            self.ROLLING_AVERAGER,
            self.AMPLIFIER,
            self.ATTENUATOR,
            self.SERIALIZER, 
            self.WS_SERVER_NODE,
        )

if __name__ == "__main__":
    graph = Demo()
    set_graph_topology(graph=graph)

    runner = lg.ParallelRunner(graph=graph)
    runner.run()
    
    
    
