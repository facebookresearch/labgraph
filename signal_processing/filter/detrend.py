#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

import logging

import numpy as np
from scipy import signal


def _get_non_zero_index(data: np.array):
    return data.nonzero()[0]


def interpolate_nan(y: np.ndarray):
    nans = np.isnan(y)
    y1 = y.copy()
    y1[nans] = np.interp(
        _get_non_zero_index(nans), _get_non_zero_index(~nans), y[~nans]
    )
    return y1


def detrend_and_offset(data: np.ndarray, fix_negative: bool = False) -> np.ndarray:
    """
    Detrend time series by subtracting from it
    a linear fit. Then offset it so the detrended
    time series is centered on the temporal mean
    of the original data.

    If `fix_negative` is True, then any data points that
    become negative after the process will be interpolated.
    Use this option when the input is DOT power measurements
    that will be logmean'd afterward.

    Input:
    - data: np.ndarray, data array of shape [n_time, n_channels]
    - fix_negative: bool, if True then after detrend and offset,
        any points that are negative will be interpolated to
        be positive. This requires the mean of the original
        data to be positive.

    Returns:
    - output: np.ndarray, same shape as data, contains
        the detrended and output signal
    """
    detrended = signal.detrend(data, axis=0)
    output = detrended + np.mean(data, axis=0, keepdims=True)
    all_nan_channels = 0

    if fix_negative:
        if np.any(np.mean(data, axis=0) < 0):
            raise ValueError("data mean is negative, cannot fix negative")
        # check how many results <=0
        n_le0 = np.sum(output <= 0)
        bad_ch = np.unique(np.argwhere(output <= 0)[:, 1])
        logging.info(f"bad_ch are {bad_ch}")
        logging.info(f"Found {n_le0} points with values <=0, interpolating")
        output[output <= 0] = np.nan

        for ch in bad_ch:
            if np.all(np.isnan(output[:, ch])):
                logging.warning("Channel all nans, skipping")
                all_nan_channels += 1
                continue
            output[:, ch] = interpolate_nan(output[:, ch])
        if all_nan_channels > 0:
            logging.warning(
                f"{all_nan_channels} channels all nans, check channel std and mean!"
            )
    return output
