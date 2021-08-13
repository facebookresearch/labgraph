#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

import asyncio
import dataclasses
import datetime
import os
import pathlib
import platform
import sys
import tempfile
import time
from typing import List, Sequence, Tuple

import labgraph as lg
import h5py
import numpy as np


SAMPLE_DATA_SIZE = 10
PLATFORM = {
    "Darwin": "mac",
    "Linux": "linux",
    "Windows": "win",
}[platform.system()]
SAMPLE_SUMMARY_DATASET_PREFIX = "sample_summary"
COUNT_DATASET_NAME = "count"

logger = lg.util.logger.get_logger(__name__)


class LoadTestConfig(lg.Config):
    duration: float = 30.0
    dynamic_size: int = 8
    output_file: str = dataclasses.field(
        default_factory=lambda: str(
            pathlib.Path(tempfile.gettempdir())
            / pathlib.Path(f"load_test_python_{PLATFORM}_{get_datestamp()}.h5")
        )
    )


class LoadTestSample(lg.TimestampedMessage):
    counter: lg.IntType(c_type=lg.CIntType.LONG_LONG)
    data: lg.NumpyType(shape=(SAMPLE_DATA_SIZE,), dtype=np.uint64)
    dynamic_data: lg.NumpyDynamicType(dtype=np.uint64)


class LoadTestPublisher(lg.Node):
    OUTPUT = lg.Topic(LoadTestSample)
    config: LoadTestConfig

    def setup(self) -> None:
        self.running = True
        self.counter = 0

    @lg.publisher(OUTPUT)
    async def publish(self) -> lg.AsyncPublisher:
        logger.info(f"Load test publisher started. (PID: {os.getpid()})")
        start_time = get_time()
        while self.running:
            current_time = get_time()
            if current_time - start_time >= self.config.duration:
                break
            yield self.OUTPUT, LoadTestSample(
                timestamp=get_time(),
                counter=self.counter,
                data=np.ones(shape=(SAMPLE_DATA_SIZE,), dtype=np.uint64),
                dynamic_data=np.ones(
                    shape=(self.config.dynamic_size // np.dtype(np.uint64).itemsize,),
                    dtype=np.uint64,
                ),
            )
            self.counter += 1

    def cleanup(self) -> None:
        self.running = False
        logger.info(f"Samples sent: {self.counter}")

        # Write number of samples sent to HDF5 file
        with h5py.File(self.config.output_file, mode="a") as output_file:
            if COUNT_DATASET_NAME not in output_file:
                count_dataset = output_file.create_dataset(
                    COUNT_DATASET_NAME,
                    shape=(1,),
                    maxshape=(None,),
                    dtype=get_count_dtype(),
                )
            else:
                count_dataset = output_file[COUNT_DATASET_NAME]
                count_dataset.resize((len(count_dataset) + 1,))

            count_dataset[-1] = (
                True,
                self.config.duration,
                self.counter,
                LoadTestSample.__message_size__ + self.config.dynamic_size,
                self.config.dynamic_size,
            )


class LoadTestSubscriberState(lg.State):
    # Tuples of sent timestamp, received timestamp, counter, dynamic size
    received_data: List[Tuple[float, float, int, int]] = dataclasses.field(
        default_factory=list
    )


class LoadTestSubscriber(lg.Node):
    INPUT = lg.Topic(LoadTestSample)
    config: LoadTestConfig
    state: LoadTestSubscriberState

    @lg.subscriber(INPUT)
    async def receive(self, sample: LoadTestSample) -> None:
        dynamic_size = 0
        for i in range(LoadTestSample.__num_dynamic_fields__):
            dynamic_size += len(sample.__sample__.dynamicParameters[i])
        self.state.received_data.append(
            (sample.timestamp, get_time(), sample.counter, dynamic_size)
        )

    @lg.background
    async def log_result(self) -> None:
        logger.info(f"Load test subscriber started. (PID: {os.getpid()})")
        logger.info(f"Writing load test output to {self.config.output_file}")

        # Wait for the duration of the load test
        await asyncio.sleep(self.config.duration)

        # Log some useful summary statistics
        min_timestamp = min(
            timestamp for timestamp, _, _, _ in self.state.received_data
        )
        max_timestamp = max(
            timestamp for timestamp, _, _, _ in self.state.received_data
        )
        total_latency = sum(
            receive_timestamp - send_timestamp
            for send_timestamp, receive_timestamp, _, _ in self.state.received_data
        )

        counters = np.array(sorted(t[2] for t in self.state.received_data))
        counter_diffs = counters[1:] - counters[:-1]
        dropped_samples = np.sum(counter_diffs - 1)

        num_samples = len(self.state.received_data)
        logger.info(f"Samples received: {num_samples}")
        logger.info(f"Sample rate: {num_samples / (max_timestamp - min_timestamp)} Hz")
        logger.info(f"Mean latency: {total_latency / num_samples} s")

        total_data = num_samples * LoadTestSample.__message_size__ + sum(
            dyn_size for _, _, _, dyn_size in self.state.received_data
        )
        logger.info(f"Data rate: {total_data / (max_timestamp - min_timestamp)} B/s")
        logger.info(
            f"Dropped samples: {dropped_samples} ({dropped_samples / (dropped_samples + num_samples)}%)",
        )

        # Write sample summaries and counts to HDF5 file
        with h5py.File(self.config.output_file, mode="a") as output_file:
            sample_summary_dataset_name = (
                f"{SAMPLE_SUMMARY_DATASET_PREFIX}_{self.config.dynamic_size}"
            )
            if sample_summary_dataset_name not in output_file:
                sample_summary_dataset = output_file.create_dataset(
                    sample_summary_dataset_name,
                    shape=(num_samples,),
                    maxshape=(None,),
                    dtype=get_sample_summary_dtype(),
                )
            else:
                sample_summary_dataset = output_file[sample_summary_dataset_name]
                sample_summary_dataset.resize(
                    (len(sample_summary_dataset) + num_samples,)
                )

            if COUNT_DATASET_NAME not in output_file:
                count_dataset = output_file.create_dataset(
                    COUNT_DATASET_NAME,
                    shape=(1,),
                    maxshape=(None,),
                    dtype=get_count_dtype(),
                )
            else:
                count_dataset = output_file[COUNT_DATASET_NAME]
                count_dataset.resize((len(count_dataset) + 1,))

            # Write sample count information
            count_dataset[-1] = (
                False,
                self.config.duration,
                num_samples,
                LoadTestSample.__message_size__ + self.config.dynamic_size,
                self.config.dynamic_size,
            )

            # Write sample summaries
            sample_summary_dataset[-num_samples:] = [
                (
                    sent_timestamp,
                    received_timestamp,
                    counter,
                )
                for sent_timestamp, received_timestamp, counter, _ in self.state.received_data
            ]
        raise lg.NormalTermination()


class LoadTest(lg.Graph):
    PUBLISHER: LoadTestPublisher
    SUBSCRIBER: LoadTestSubscriber

    config: LoadTestConfig

    def setup(self) -> None:
        self.PUBLISHER.configure(self.config)
        self.SUBSCRIBER.configure(self.config)

    def connections(self) -> lg.Connections:
        return ((self.PUBLISHER.OUTPUT, self.SUBSCRIBER.INPUT),)

    def process_modules(self) -> Sequence[lg.Module]:
        return (self.PUBLISHER, self.SUBSCRIBER)


def get_time() -> float:
    # time.perf_counter() isn't system-wide on Windows Python 3.6:
    # https://bugs.python.org/issue37205
    return time.time() if PLATFORM == "win" else time.perf_counter()


def get_datestamp() -> str:
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")


def get_sample_summary_dtype() -> np.dtype:
    return np.dtype(
        [
            ("sent_timestamp", np.float64),
            ("received_timestamp", np.float64),
            ("counter", np.uint64),
        ]
    )


def get_count_dtype() -> np.dtype:
    return np.dtype(
        [
            ("sent", np.bool),
            ("duration", np.float64),
            ("count", np.uint64),
            ("size", np.uint64),
            ("dynamic_size", np.uint64),
        ]
    )


def run_many_dynamic_sizes() -> None:
    dynamic_sizes = np.logspace(3, 23, base=2, num=21, dtype=np.uint64)
    config = LoadTestConfig.fromargs(
        [arg for arg in sys.argv[1:] if arg != "--many-dynamic-sizes"]
    )
    for dynamic_size in dynamic_sizes:
        logger.info(f"Running load test for dynamic size: {dynamic_size}")
        runner = lg.ParallelRunner(
            graph=LoadTest(config=config.replace(dynamic_size=int(dynamic_size)))
        )
        runner.run()


if __name__ == "__main__":
    if "--many-dynamic-sizes" in sys.argv:
        run_many_dynamic_sizes()
    else:
        lg.run(LoadTest)
