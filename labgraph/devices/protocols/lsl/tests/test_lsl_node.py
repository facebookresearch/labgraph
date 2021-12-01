from pylsl import StreamInfo, StreamOutlet, StreamInlet, resolve_stream
from labgraph.runners.parallel_runner import ParallelRunner
import pytest
import asyncio
import time
from multiprocessing import Process
from typing import Sequence

from labgraph.graphs import (
    AsyncPublisher,
    Config,
    Connections,
    Graph,
    Module,
    Node,
    Topic,
    publisher,
    subscriber
)

from labgraph.runners import LocalRunner, NormalTermination, ParallelRunner
from labgraph.util.testing import get_test_filename, local_test
from labgraph.devices.protocols.lsl import LSLMessage
from labgraph.devices.protocols.lsl.lsl_poller_node import LSLPollerConfig, LSLPollerNode
from labgraph.devices.protocols.lsl.lsl_sender_node import LSLSenderConfig, LSLSenderNode

NUM_MESSAGES = 10
SAMPLE_RATE = 10

DATA_DELIMITER = "\n"
samples = [0.1, 1.1, 2.3, 4.4, 5.5, 6.6, 7.5, 7.7, 8.8, 9.9]


class MySinkConfig(Config):
    output_filename: str = get_test_filename()


class MySink(Node):
    """
    Convenience node for receiving messages from a `LSLSenderNode`.
    """

    TOPIC = Topic(LSLMessage)
    config: MySinkConfig

    def setup(self) -> None:
        self.output_file = open(self.config.output_filename, "w+")
        self.num_received = 1

    @subscriber(TOPIC)
    async def sink(self, message: LSLMessage) -> None:
        for value in message.data:
            value_str = str(value)
            self.output_file.write(value_str)
            self.output_file.write(DATA_DELIMITER)
        self.num_received += 1

        if self.num_received == NUM_MESSAGES:
            raise NormalTermination()

    def cleanup(self) -> None:
        self.output_file.close()


class MySourceConfig(Config):
    should_terminate: bool = True


class MySource(Node):
    """
    Convenience node for supplying messages to a LSLSenderNode
    """
    TOPIC = Topic(LSLMessage)
    config: MySourceConfig

    @publisher(TOPIC)
    async def source(self) -> AsyncPublisher:

        yield self.TOPIC, LSLMessage(samples)
        await asyncio.sleep(1/SAMPLE_RATE)

        if self.config.should_terminate:
            raise NormalTermination()


# send messages
def write_sample_to_lsl() -> None:
    srate = 100
    name = 'Mock LSL Sender'
    type = 'EEG'
    n_channels = 10
    info = StreamInfo(name, type, n_channels, srate, 'float32', 'myuid34234')
    outlet = StreamOutlet(info)
    print("now sending data...")
    max_iter = 300
    iter = 0
    while iter < max_iter:
        outlet.push_sample(samples)
        iter += 1
        time.sleep(0.01)


def recv_samples_from_lsl(output_fname: str) -> None:
    print("looking for an EEG Stream")
    streams = resolve_stream('type', 'TEST')
    inlet = StreamInlet(streams[0])

    with open(output_fname, "w+") as output_file:
        sample, timestamp = inlet.pull_sample()
        for value in sample:
            value_str = str(value)
            output_file.write(value_str)
            output_file.write(DATA_DELIMITER)
        output_file.close()


@local_test
def test_lsl_poller_node() -> None:
    class LSLPollerGraphConfig(Config):
        output_filename: str

    class LSLPollerGraph(Graph):
        MY_SOURCE: LSLPollerNode
        MY_SINK: MySink
        config: LSLPollerGraphConfig

        def setup(self) -> None:
            self.MY_SOURCE.configure(
                LSLPollerConfig(
                    type='EEG'
                )
            )
            self.MY_SINK.configure(
                MySinkConfig(output_filename=self.config.output_filename)
            )

        def connections(self) -> Connections:
            return ((self.MY_SOURCE.topic, self.MY_SINK.TOPIC),)

    graph = LSLPollerGraph()
    output_filename = get_test_filename()
    graph.configure(
        LSLPollerGraphConfig(
            output_filename=output_filename
        )
    )
    runner = LocalRunner(module=graph)
    p = Process(target=write_sample_to_lsl, args=())
    p.start()
    runner.run()
    p.join()

    with open(output_filename, "r") as f:
        data = f.read()
    recieved_data = set(data.strip(DATA_DELIMITER).split(DATA_DELIMITER))
    assert len(recieved_data) > 0
    assert len(samples) == len(recieved_data)


@local_test
def test_lsl_sender_node() -> None:
    class LSLSenderGraph(Graph):
        MY_SOURCE: MySource
        MY_SINK: LSLSenderNode

        config: LSLSenderConfig

        def setup(self) -> None:
            self.MY_SOURCE.configure(MySourceConfig())
            self.MY_SINK.configure(self.config)

        def connections(self) -> Connections:
            return ((self.MY_SOURCE.TOPIC, self.MY_SINK.topic),)

    output_filename = get_test_filename()
    graph = LSLSenderGraph()
    graph.configure(LSLSenderConfig(
        name='Test',
        type='TEST',
        n_channels=NUM_MESSAGES,
        unique_identifier='12345QE'
    ))
    runner = LocalRunner(module=graph)
    p = Process(
        target=recv_samples_from_lsl, args=(output_filename,)
    )
    p.start()
    runner.run()
    p.join()

    with open(output_filename, "r") as f:
        data = f.read()

    recieved_data = set(data.strip(DATA_DELIMITER).split(DATA_DELIMITER))
    assert len(recieved_data) > 0
    assert len(samples) == len(recieved_data)


@local_test
def test_lsl_send_and_poll() -> None:
    class LSLGraphConfig(Config):
        output_filename: str

    class LSLGraph(Graph):
        DF_SOURCE: MySource
        LSL_SENDER: LSLSenderNode
        LSL_POLLER: LSLPollerNode
        DF_SINK: MySink

        def setup(self) -> None:
            self.DF_SOURCE.configure(MySourceConfig(should_terminate=True))
            self.LSL_SENDER.configure(
                LSLSenderConfig(
                    name='Test',
                    type='EEG',
                    n_channels=NUM_MESSAGES,
                    unique_identifier='12345QE'
                )
            )
            self.LSL_POLLER.configure(
                LSLPollerConfig(
                    type='EEG'
                )
            )
            self.DF_SINK.configure(
                MySinkConfig(output_filename=self.config.output_filename)
            )

        def connections(self) -> Connections:
            return(
                (self.DF_SOURCE.TOPIC, self.LSL_SENDER.topic),
                (self.LSL_POLLER.topic, self.DF_SINK.TOPIC)
            )

        def process_modules(self) -> Sequence[Module]:
            return (self.DF_SOURCE, self.LSL_SENDER, self.LSL_POLLER,
                    self.DF_SINK)

    output_filename = get_test_filename()
    graph = LSLGraph()
    graph.configure(
        LSLGraphConfig(
            output_filename=output_filename
        )
    )
    runner = ParallelRunner(graph=graph)
    runner.run()

    with open(output_filename, "r") as f:
        data = f.read()
    recieved_data = set(data.strip(DATA_DELIMITER).split(DATA_DELIMITER))
    assert len(recieved_data) > 0
    assert len(samples) == len(recieved_data)
