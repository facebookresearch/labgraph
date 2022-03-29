import labgraph as lg
from typing import Tuple

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
from extensions.yaml_support.labgraph_monitor.generate_lg_monitor.generate_lg_monitor import generate_graph_topology

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

    # Provide graph topology with `generate_labgraph_monitor()`
    def set_topology(self, topology: SerializedGraph) -> None:
        self._topology = topology

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

if __name__ == "__main__":
    graph = Demo()
    topology = generate_graph_topology(graph=graph)
    graph.set_topology(topology)

    runner = lg.ParallelRunner(graph=graph)
    runner.run()