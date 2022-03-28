#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

""" Node for a IIR filter for causal Faucet """

import asyncio
import logging
import time
from dataclasses import field
from typing import List, Optional, Union

import labgraph as lg
import numpy as np
from ...messages.generic_signal_sample import SignalSampleMessage
from ...filter.iir_filters import CausalButterworth


# Define states and configs
class CausalButterFilterNodeConfig(lg.Config):
    """Sampling frequency in Hz

    sample_rate: sampling frequency in Hz
    highpass_cutoff: highpass cutoff in Hz
    highpass_order: order of highpass filter
    lowpass_cutoffs: List of lowpass filter cutoff frequencies.
        length of this list is the total order of lowpass

    Online estimate of sampling frequency:

    If sample_rate was not given when node is initialized,
    the filter node will fill a buffer of length `initial_buffer_len`
    messages, and derive the sample_rate from their timestamps. This
    assumes uniform sampling. Default is 10 samples, in which case the
    output will be non-null at the second sample.
    """

    sample_rate: float = -1.0
    initial_buffer_len: int = 10

    highpass_cutoff: Optional[float] = 0.01
    highpass_order: Optional[int] = 5
    lowpass_cutoffs: List = field(default_factory=list)

    """
    Option to invert the input sample.
    Faucet expects the input to bandpass is -log(power_measurement).
    Node outputs log(power_measurements). If bandpass is the first
    filtering stage, the default `invert_input=True` would take care
    of the inversion.

    If used for something else (e.g. IMU, etc), set this appropriately!
    """
    invert_input: bool = True
    pass_through: bool = False

    def __post_init__(self):
        super().__post_init__()
        if self.sample_rate < 0 and self.initial_buffer_len <= 0:
            raise ValueError(
                "initial_buffer_len needs to be greater than 0 when sample rate unspecified"
            )


class DefaultBandpassConfigGenerator:
    def getConfig():
        return CausalButterFilterNodeConfig(
            sample_rate=-1.0,  # estimate sample rate
            initial_buffer_len=10,
            highpass_cutoff=0.01,
            highpass_order=5,
            lowpass_cutoffs=[0.1, 0.1, 0.1, 0.1, 0.1],
            invert_input=True,
            pass_through=False,
        )


class CausalButterFilterState(lg.State):
    initial_buffer: List[SignalSampleMessage] = field(default_factory=list)
    filters: List[CausalButterworth] = field(default_factory=list)
    sample_rate: float = -1.0


class CausalButterFilterNode(lg.Node):
    """
    If the input SignalSampleMessage has an empty
    `sample_timestamp`, then it's assumed this is the
    first casual filter of the signal processing chain
    and follows directly after a data source.

    Otherwise, the sample rate estimation will be calculated
    from the `sample_timestamp` field of the SignalSampleMessage.

    This is because in the second case, the sample rate is best
    estimated from the timestamps of the raw messages directly
    from the data source.
    """

    # Subscribed topics
    INPUT = lg.Topic(SignalSampleMessage)
    TERMINATION_TOPIC = lg.Topic(lg.TerminationMessage)

    # Published topics
    OUTPUT = lg.Topic(SignalSampleMessage)

    state: CausalButterFilterState
    config: CausalButterFilterNodeConfig

    def setup(self) -> None:
        self._shutdown = asyncio.Event()
        # Have to be assigned here because config cannot be modified in runtime
        self.state.sample_rate = self.config.sample_rate

    @lg.subscriber(TERMINATION_TOPIC)
    def terminate(self, message: lg.TerminationMessage) -> None:
        self._shutdown.set()
        raise lg.NormalTermination()

    def _init_filter_class(self, message: SignalSampleMessage) -> bool:
        # Returns True if filter class is initialized

        if len(self.state.filters) > 0:
            return True

        self.state.initial_buffer.append(message)
        if self.state.sample_rate < 0:
            if len(self.state.initial_buffer) <= self.config.initial_buffer_len:
                return False
            if not np.isnan(self.state.initial_buffer[0].sample_timestamp):
                timestamps = np.array(
                    [message.sample_timestamp for message in self.state.initial_buffer]
                )
            else:
                timestamps = np.array(
                    [message.timestamp for message in self.state.initial_buffer]
                )
            self.state.sample_rate = 1 / np.mean(np.diff(timestamps))
            logging.info(f"estimated sample rate = {self.state.sample_rate}Hz")

        self._init_and_run_filters()
        return True

    def _init_and_run_filters(self):
        # Initialize filters and run it for all but last sample in initial_buffer
        if len(self.state.filters) != 0:
            logging.warning(
                "_init_filters called when self.state.filters is not empty, skipping!"
            )
            return
        # shape is [n_channel, ]
        # initial state of each cascaded filter is calculated by taking
        # the steady-state value of the previous filter in response to
        # that previous filter's initial state!
        initial_state = self.state.initial_buffer[0].sample
        # initialize highpass filter
        if (
            self.config.highpass_cutoff is not None
            and self.config.highpass_order is not None
        ):
            self.state.filters.append(
                CausalButterworth(
                    first_time_sample=initial_state,
                    cutoff=self.config.highpass_cutoff,
                    sample_freq=self.state.sample_rate,
                    btype="highpass",
                    order=self.config.highpass_order,
                )
            )
            initial_state = self.state.filters[-1].process_sample(initial_state)
        # initialize lowpass filters
        if len(self.config.lowpass_cutoffs) > 0:
            for cutoff in self.config.lowpass_cutoffs:
                self.state.filters.append(
                    CausalButterworth(
                        first_time_sample=initial_state,
                        cutoff=cutoff,
                        sample_freq=self.state.sample_rate,
                        btype="lowpass",
                        order=1,
                    )
                )
                initial_state = self.state.filters[-1].process_sample(initial_state)
        for buffered_message in self.state.initial_buffer[:-1]:
            _ = self._process_sample(buffered_message.sample)

    def _process_sample(self, sample: np.ndarray) -> np.ndarray:
        # Run process_sample through the entire cascade of filters
        output = sample
        for filt in self.state.filters:
            output = filt.process_sample(output)
        return output

    @lg.subscriber(INPUT)
    @lg.publisher(OUTPUT)
    async def run_filter(self, message: SignalSampleMessage) -> lg.AsyncPublisher:
        """
        Assume message.sample is np.ndarray with dimension [n_channels, ]
        """

        if self.config.invert_input:
            message = SignalSampleMessage(message.timestamp, -message.sample)

        if self.config.pass_through:
            yield self.OUTPUT, message
            return

        if not self._init_filter_class(message):
            return

        filtered_sample = self._process_sample(message.sample)
        """
        Return the filtered sample
            filtered_sample now has to be reshaped to (channel, time)
            because HDF5 file requires it that way
        """
        sample_timestamp = (
            message.timestamp
            if np.isnan(message.sample_timestamp)
            else message.sample_timestamp
        )
        yield self.OUTPUT, SignalSampleMessage(
            timestamp=time.time(),
            sample_timestamp=sample_timestamp,
            sample=filtered_sample.reshape((-1, 1)),
        )
