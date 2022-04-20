#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserve

from labgraph.examples.graph_w_logging import Demo as GraphWLogging
from graphviz_support import generate_graphviz
import pathlib


if __name__ == '__main__':
    graph_w_logging = GraphWLogging()
    out_dir: str = pathlib.Path(__file__).parent.absolute()
    generate_graphviz(
        graph_w_logging,
        f'{out_dir}/output/graph_w_logging.svg'
    )
