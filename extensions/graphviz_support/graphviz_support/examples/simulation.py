#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserve

from labgraph.examples.simulation import Demo as SimulationGraph
from ..generate_graphviz.generate_graphviz import generate_graphviz
import pathlib


if __name__ == '__main__':
    simulation = SimulationGraph()
    out_dir: str = pathlib.Path(__file__).parent.absolute()
    generate_graphviz(
        simulation,
        f'{out_dir}/output/simulation.svg'
    )
