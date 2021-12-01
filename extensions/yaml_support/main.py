from .yamlify import yamlify
from typing import List


if __name__ == "__main__":

    paths: List[str] = [
        "labgraph/examples/simple_viz.py",
        "labgraph/examples/simple_viz_fixed_rate.py",
        "labgraph/examples/simple_viz_zmq.py",
        "labgraph/examples/simulation.py",
    ]

    for path in paths:
        yamlify(path, f"{path}_yamlified")
