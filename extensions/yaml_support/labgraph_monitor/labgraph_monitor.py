#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved,

import labgraph as lg
from .generate_lg_monitor.generate_lg_monitor import generate_graph_topology, set_graph_topology
from .server.lg_monitor_server import run_topology

class LabgraphMonitor:
    """
    A class that serves as a facade for 
    LabGraph Monitor's Back-End functions
    """

    def __init__(self, graph: lg.Graph) -> None:
        self.graph = graph

    def stream_graph_topology(self) -> None:
        """
        Stream graph topology via WebSockets
        """
        topology = generate_graph_topology(self.graph)
        run_topology(topology)
    
    def stream_real_time_graph(self) -> None:
        """
        Stream graph topology and real-time
        messages via WebSockets
        """
        set_graph_topology(self.graph)

        runner = lg.ParallelRunner(self.graph)
        runner.run()