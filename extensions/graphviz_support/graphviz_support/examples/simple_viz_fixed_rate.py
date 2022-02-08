#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserve

from labgraph.examples.simple_viz_fixed_rate import (
    Demo as SimpleVizFixedRateGraph
)
from ..generate_graphviz.generate_graphviz import generate_graphviz
import pathlib


if __name__ == '__main__':
    simple_viz_fixed_rate_graph = SimpleVizFixedRateGraph()
    out_dir: str = pathlib.Path(__file__).parent.absolute()
    generate_graphviz(
        simple_viz_fixed_rate_graph,
        f'{out_dir}/output/simple_viz_fixed_rate.svg'
    )
