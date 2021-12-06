#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

import time
from pathlib import Path
from typing import Dict, Sequence

import h5py
from MyCPPNodes import MyCPPSink, MyCPPSource  # type: ignore

from ...graphs.config import Config
from ...graphs.cpp_node import CPPNodeConfig
from ...graphs.graph import Graph
from ...graphs.group import Connections
from ...graphs.method import subscriber
from ...graphs.module import Module
from ...graphs.node import Node
from ...graphs.topic import Topic
from ...messages.message import Message
from ...runners.exceptions import NormalTermination
from ...runners.parallel_runner import ParallelRunner
from ...util.testing import get_test_filename, local_test


class MyMessage(Message):
    value: int


class MySinkConfig(Config):
    filename: str


class MyPythonSink(Node):
    C = Topic(MyMessage)

    config: MySinkConfig

    def setup(self) -> None:
        self.messages_seen: int = 0

    @subscriber(C)
    def sink(self, message: MyMessage) -> None:
        with open(self.config.filename, "a") as f:
            f.write(str(message.value) + "\n")
        self.messages_seen += 1
        if self.messages_seen == MyCPPSource.NUM_SAMPLES:
            time.sleep(2)
            raise NormalTermination()


class MyGraphConfig(Config):
    python_filename: str
    cpp_filename: str


class MyMixedGraph(Graph):
    CPP_SOURCE: MyCPPSource
    CPP_SINK: MyCPPSink
    PYTHON_SINK: MyPythonSink

    config: MyGraphConfig

    def setup(self) -> None:
        self.CPP_SINK.configure(CPPNodeConfig(args=[self.config.cpp_filename]))
        self.PYTHON_SINK.configure(MySinkConfig(filename=self.config.python_filename))

    def connections(self) -> Connections:
        return (
            (self.CPP_SOURCE.A, self.CPP_SINK.B),
            (self.CPP_SOURCE.A, self.PYTHON_SINK.C),
        )

    def process_modules(self) -> Sequence[Module]:
        return [self.CPP_SOURCE, self.CPP_SINK, self.PYTHON_SINK]

    def logging(self) -> Dict[str, Topic]:
        return {
            "cpp_source": self.CPP_SOURCE.A,
            "cpp_sink": self.CPP_SINK.B,
            "python_sink": self.PYTHON_SINK.C,
        }


@local_test
def test_cpp_graph() -> None:
    """
    Tests that we can run a graph with both C++ and Python nodes, and read the results
    on disk.
    """
    # Run the graph
    graph = MyMixedGraph()
    python_filename = get_test_filename()
    cpp_filename = get_test_filename()
    graph.configure(
        MyGraphConfig(python_filename=python_filename, cpp_filename=cpp_filename)
    )
    runner = ParallelRunner(graph=graph)
    # Get the HDF5 log path to verify the logs later
    output_path = str(  # noqa: F841
        Path(runner._options.logger_config.output_directory)
        / Path(f"{runner._options.logger_config.recording_name}.h5")
    )
    runner.run()

    # Check C++ sink output
    cpp_nums = set(range(MyCPPSource.NUM_SAMPLES))
    with open(cpp_filename, "r") as f:
        for line in f:
            num = int(line.strip())
            cpp_nums.remove(num)

    assert len(cpp_nums) == 0, f"Missing numbers in C++ sink output: {cpp_nums}"

    # Check Python sink output
    python_nums = set(range(MyCPPSource.NUM_SAMPLES))
    with open(python_filename, "r") as f:
        for line in f:
            num = int(line.strip())
            if num in python_nums:
                python_nums.remove(num)

    assert (
        len(python_nums) == 0
    ), f"Missing numbers in Python sink output: {python_nums}"

    # Check HDF5 logger output
    with h5py.File(output_path, "r") as h5py_file:
        for hdf5_path in ("cpp_source", "cpp_sink", "python_sink"):
            dataset = h5py_file[hdf5_path]
            assert dataset.shape == (MyCPPSource.NUM_SAMPLES,)
            dataset_nums = {int(num[0]) for num in dataset}
            assert dataset_nums == set(range(MyCPPSource.NUM_SAMPLES))
