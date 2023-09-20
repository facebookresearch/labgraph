#!/usr/bin/env python3
# # -*- coding: utf-8 -*-
import dataclasses
import pytest
import labgraph as lg
from ..nodeDelsys import configDelsys, nodeDelsys, stateDelsys, messageDelsysState

DATA_SHAPE = (8, 26)
SAMPLE_RATE = 1926.0
MAX_NUM_RESULTS = 10


def test_get_node() -> None:
    """
    Test NodeTestHarness.get_node()
    """
    harness = lg.NodeTestHarness(nodeDelsys)
    with harness.get_node(config=configDelsys(sample_rate=SAMPLE_RATE),
                          state=stateDelsys(Connect=False,
                                            Pair=False,
                                            Scan=False,
                                            Start=False,
                                            Stop=False,
                                            Ready=False)) as node:
        # Ensure node is of correct type
        assert isinstance(node, nodeDelsys)
        # Check the node has its config set
        assert node.config.asdict() == {"sample_rate": SAMPLE_RATE}
        # Check the node has its state set
        assert dataclasses.asdict(node.state) == {"Connect": False,
                                                  "Pair": False,
                                                  "Scan": False,
                                                  "Start": False,
                                                  "Stop": False,
                                                  "Ready": False}


def test_run_async_max_num_results() -> None:
    """
    Test passing max_num_results to run_async
    """
    harness = lg.NodeTestHarness(nodeDelsys)
    with harness.get_node(config=configDelsys(sample_rate=SAMPLE_RATE),
                          state=stateDelsys(Connect=False,
                                            Pair=False,
                                            Scan=False,
                                            Start=False,
                                            Stop=False,
                                            Ready=False)) as node:

        lg.run_async(node.getDelsysState, args=[messageDelsysState(timestamp=1.0,
                                                                   setConnectState=False,
                                                                   setPairState=False,
                                                                   setScanState=False,
                                                                   setStartState=False,
                                                                   setStopState=False)])
        assert node.state.Connect is False
        assert node.state.Pair is False
        assert node.state.Scan is False
        assert node.state.Start is False
        assert node.state.Stop is False
        assert node.state.Ready is False
