#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

"""
Node for performing logmean online
"""

import time
from dataclasses import field
from typing import List, Optional

import labgraph as lg
import numpy as np
from ...messages.generic_signal_sample import SignalSampleMessage


class LogMeanNodeConfig(lg.Config):
    # When LogarithmNode is part of a bigger group, setting
    # this to True provides an easy way to turn off
    # this stage.
    pass_through: bool = False


class LogMeanNodeState(lg.State):
    # initialized to nan
    last_nonzero_values: Optional[np.ndarray] = None


class LogmeanNode(lg.Node):
    """
    The logic here follows closedly with that of `compute_log_all_samples`:

    Instead of taking the -log(x / mean(x)), we directly take the -log of a channel's
    incoming signal value (assumed to be in units of Watt).

    If the incoming signal value is 0 or negative, this is assumed to be an anomaly,
    either the sensor is bad (even noise has non-zero energy!) or turned off.

    In this case, we impute this value with the last non-zero signal value for this
    channel.

    If the first value we receive for a channel is 0, then we return 0 for the
    logmean result, and do not update the last nonzero-value for this channel.
    """

    # Subscribed topics
    INPUT = lg.Topic(SignalSampleMessage)

    # Published topics
    OUTPUT = lg.Topic(SignalSampleMessage)

    state: LogMeanNodeState
    config: LogMeanNodeConfig

    @lg.subscriber(INPUT)
    @lg.publisher(OUTPUT)
    async def get_logmean(self, message: SignalSampleMessage) -> lg.AsyncPublisher:
        if self.config.pass_through:
            yield self.OUTPUT, message
        else:
            if self.state.last_nonzero_values is None:
                self.state.last_nonzero_values = np.ones(message.sample.shape) * np.nan

            output = np.copy(message.sample)

            # Find 0 or negative channel values
            is_less_eq_zero = output <= 0
            output[~is_less_eq_zero] = -np.log10(output[~is_less_eq_zero])
            # update the last_nonzero_values
            self.state.last_nonzero_values[~is_less_eq_zero] = message.sample[
                ~is_less_eq_zero
            ]

            # missing value imputation, no need to update state for these
            can_impute = (~np.isnan(self.state.last_nonzero_values)) & is_less_eq_zero
            output[can_impute] = -np.log10(self.state.last_nonzero_values[can_impute])

            # deal with the non-imputable -- output will be 0, these are just bad channels!
            cant_impute = np.isnan(self.state.last_nonzero_values) & is_less_eq_zero
            output[cant_impute] = 0

            yield self.OUTPUT, SignalSampleMessage(
                timestamp=time.time(),
                sample_timestamp=message.timestamp,
                sample=output,
            )
