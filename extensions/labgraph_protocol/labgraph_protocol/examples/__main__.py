#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

import argparse
import typing

import labgraph as lg
from labgraph_protocol.protocol_node import (
    ProtocolNode,
    ProtocolNodeConfig,
)
from labgraph_protocol.qt_node import (
    FULLSCREEN,
    QtNode,
    QtNodeConfig,
    WINDOW_SIZE_T,
)

PROTOCOL_MODULE = "labgraph_protocol.examples.{0}"


class UIGraphConfig(lg.Config):
    protocol_name: str
    window_size: WINDOW_SIZE_T


class UIGraph(lg.Graph):
    PROTOCOL_NODE: ProtocolNode
    QT_NODE: QtNode

    def setup(self) -> None:
        protocol_config = ProtocolNodeConfig(
            module=PROTOCOL_MODULE.format(self.config.protocol_name)
        )
        self.PROTOCOL_NODE.configure(protocol_config)
        qt_config = QtNodeConfig(
            module=PROTOCOL_MODULE.format(self.config.protocol_name),
            window_size=self.config.window_size,
        )
        self.QT_NODE.configure(qt_config)

    def connections(self) -> lg.Connections:
        return (
            (self.PROTOCOL_NODE.CURRENT_TRIAL_TOPIC, self.QT_NODE.CURRENT_TRIAL_TOPIC),
            (self.QT_NODE.END_TRIAL_TOPIC, self.PROTOCOL_NODE.END_TRIAL_TOPIC),
            (self.QT_NODE.READY_TOPIC, self.PROTOCOL_NODE.READY_TOPIC),
        )

    def process_modules(self) -> typing.Sequence[lg.Module]:
        return (
            self.PROTOCOL_NODE,
            self.QT_NODE,
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("protocol_name")
    parser.add_argument("--fullscreen", action="store_true")
    args = parser.parse_args()
    window_size = FULLSCREEN if args.fullscreen else (1280, 720)
    graph = UIGraph()
    graph.configure(
        UIGraphConfig(protocol_name=args.protocol_name, window_size=window_size)
    )
    runner = lg.ParallelRunner(graph=graph)
    runner.run()
