#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

import random
import time
from typing import Dict, Tuple

import labgraph as lg

# Note: Message has to be defined outside of the `__main__` module
from .random_float_message import RandomFloatMessage


class RandomFloatGenerator(lg.Node):
    """
    Generates messages with random float data
    """

    OUTPUT = lg.Topic(RandomFloatMessage)

    @lg.publisher(OUTPUT)
    async def output(self) -> lg.AsyncPublisher:
        for _ in range(10):
            yield self.OUTPUT, RandomFloatMessage(
                timestamp=time.time(), data=random.random()
            )
        raise lg.NormalTermination()


class Demo(lg.Graph):
    """
    A simple graph showing how we can log data from named topics.
    - Logs to an h5 file in the current directory.
    """

    GENERATOR: RandomFloatGenerator

    def process_modules(self) -> Tuple[lg.Module, ...]:
        return (self.GENERATOR,)

    def logging(self) -> Dict[str, lg.Topic]:
        return {"random_data": self.GENERATOR.OUTPUT}


if __name__ == "__main__":
    graph = Demo()
    options = lg.RunnerOptions(
        logger_config=lg.LoggerConfig(
            output_directory="./",
            recording_name="graph_w_logging",
        ),
    )
    runner = lg.ParallelRunner(graph=graph, options=options)
    runner.run()
