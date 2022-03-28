#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

from typing import Tuple, Union

import numpy as np
from scipy.signal import (
    butter,
    filtfilt,
    lfilter,
    sosfilt,
    sosfiltfilt,
    sosfilt_zi,
)

from .signal_transforms import filter_group_delay


def butter_coefficients(
    cutoff: Union[float, list], fs: float, btype: str, order=4
) -> Tuple[np.ndarray, np.ndarray]:
    """Butterworth filter coefficients

    Args:
    ----------
    cutoff: float or list of floats
        Cutoff frequency in Hz (e.g. 3 Hz)
    fs: float
        Sampling frequency in Hz
    btype: str
        Type of filter
        Options: ['high', 'low', 'pass', 'stop']
        'high': highpass
        'low': lowpass
        'pass': bandpass
        'stop': bandstop
    order: int
        Order of the filter

    Returns:
    ----------
    b, a : ndarray, ndarray
        Numerator and denominator polynomials
        of the IIR filter
    """

    # calculate the nyquist frequency
    nyquist = fs / 2.0
    # normalize
    normalized_cutoff = np.asarray(cutoff) / nyquist
    # calculate coefficients - analog=False to return a filter defined
    # in z-domain, otherwise it's defined in s-domained and transformed
    # through bi-linear transformation
    b, a = butter(order, normalized_cutoff, btype=btype, analog=False)
    return b, a


def butterworth_filter(
    data: np.ndarray,
    cutoff: Union[float, list],
    fs: float,
    btype: str,
    axis: int = -1,
    noDelay: bool = True,
    order: int = 4,
    **kwargs,
) -> np.ndarray:
    """Butterworth filter using transfer function (tf) implementation.
    For order higher than 4, it's recommended to use `butterworth_sos_filter`
    for numerical stability.

    Please see butter_coefficients for details
    in other attributes.

    Args:
    ----------
    data: np.ndarray, array of data you want to filter. Last dimension
        assumed to be time, following conventions of `lfilter` and `filtfilt`
        Assumed to be of dimension [n_channels, n_time_samples]

    axis: dimension along which to apply the filter, same as the option
        in `lfilter` and `filtfilt`.
        If data is [n_time_samples, n_channels], then axis should be 0.
        If data is [n_channels, n_time_samples], then axis is 1 or -1 (default).

    noDelay: flag if true, apply filter using `filtfilt`, which is zero-phase delay.
        This means the filtered signal is not delayed w.r.t input.
        Otherwise, filter is applied using `lfilter`.

        `lfilter` with butterworth should be linear phase in the passband.
        `filtfilt` is guaranteed to be zero-phase, and by extension linear phase.

        By default with noDelay=False, `lfilter` output does not start at the
        same initial value as the data input. Pass in values for 'zi' if this
        is desired (values can be generated with `lfilter_zi`)

    cutoff, fs, btype, order: See `butter_coefficients`.

    **kwargs: Extra keyword args for `lfilter` (zi) or `filtfilt` (padtype, padlen)

    Returns:
    --------
    out: np.ndarray, array of the filtered data. Same shape as data.
    """

    b, a = butter_coefficients(cutoff, fs, btype, order)

    if noDelay:
        out = filtfilt(b, a, data, axis=axis, **kwargs)
    else:
        out = lfilter(b, a, data, axis=axis, **kwargs)
    return out


def butter_sos(
    cutoff: Union[float, list], fs: float, btype: str, order: int = 4
) -> np.ndarray:
    """Butterworth filter second-order section coefficients (sos)

    Args:
    ----
    cutoff: float or list of floats
        Cutoff frequency in Hz (e.g. 3 Hz)
    fs: float
        Sampling frequency in Hz
    btype: str
        Type of filter
        Options: ['high', 'low', 'pass', 'stop']
        'high': highpass
        'low': lowpass
        'pass': bandpass
        'stop': bandstop
    order: int
        Order of the filter

    Returns:
    ----------
    sos : ndarray of second-order filter coefficients, must have shape (n_sections, 6).
          Each row corresponds to a second-order section, with the first three columns
          providing the numerator coefficients and the last three providing the
          denominator coefficients.
    """
    nyq = fs / 2.0
    normalized_cutoff = np.asarray(cutoff) / nyq
    sos = butter(order, normalized_cutoff, btype, analog=False, output="sos")
    return sos


def butterworth_sos_filter(
    data: np.ndarray,
    cutoff: Union[float, list],
    fs: float,
    btype: str,
    axis: int = -1,
    noDelay: bool = True,
    order: int = 4,
    **kwargs,
) -> np.ndarray:
    """Butterworth filter using second-order sections (sos) implementation.
    This is suitable for all frequency and filter order. However, for order
    less than 4, use `butterworth_filter` for slightly better performance.

    Please see butter_sos for details in other attributes.

    Args:
    ----------
    data: np.ndarray, array of data you want to filter. Last dimension
        assumed to be time, following conventions of `lfilter` and `filtfilt`
        Assumed to be of dimension [n_channels, n_time_samples]

    axis: dimension along which to apply the filter, same as the option
        in `sosfilt` and `sosfiltfilt`.
        If data is [n_time_samples, n_channels], then axis should be 0.
        If data is [n_channels, n_time_samples], then axis is 1 or -1 (default).

    noDelay: flag if true, apply filter using `sosfiltfilt`, results
        in zero-phase delay w.r.t input. Otherwise, filter is applied
        using `sosfilt`.

        Using `sosfiltfilt` guarantees zero-phase and linear phase.
        Using `sosfilt` with butterworth gives maximum linear-phase in the passband.

        By default with noDelay=False, `sos_filt` output does not start at the
        same initial value as the data input. Pass in values for 'zi' if this
        is desired (values can be generated with `sosfilt_zi`)

    cutoff, fs, btype, order: See `butter_sos`.

    **kwargs: Extra keyword args for `sosfilt` (zi), `sosfiltfilt` (padtype, padlen),

    Returns:
    --------
    out: np.ndarray, array of the filtered data. Same shape as data.
    """
    sos = butter_sos(cutoff=cutoff, fs=fs, btype=btype, order=order)

    if noDelay:
        # sosfiltfilt
        out = sosfiltfilt(sos, data, axis, **kwargs)
        return out
    else:
        # sosfilt, with zi
        out = sosfilt(sos, data, axis, **kwargs)
    return out


def butter_group_delay(
    cutoff: np.ndarray, fs: float, btype: str, order: int, N: int = 2048
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Return frequency in Hz (ranging 0 to fs/2),
    and group delay in samples
    """
    sos_butter = butter_sos(cutoff, fs, btype, order)
    freq, group_delay = filter_group_delay(sos_butter, N, fs, sos=True)
    return freq, group_delay


def exponential_moving_average(x: np.ndarray, y_prev: np.ndarray, N: int) -> np.ndarray:
    """EMA: Exponential Moving Average

    From the paper:
    "Moving Average Convergence Divergence filter preprocessing for
    real-time event-related peak activity onset detection:
    application to fNIRS signals"

    Equations:
    y_t = EMA(x) = \frac{2}{N+1} x_t + \frac{N-1}{N+1} y_{t-1}

    Arguments:
    ----------
    x: raw signal input at time t
    y_prev: filtered signal at time t-1
    N: parameter 1 = how many time samples to use for moving average

    Returns:
    ----------
    y: filtered signal at time t
    """

    coeff_x = 2 / (N + 1)
    coeff_y_prev = (N - 1) / (N + 1)
    y = coeff_x * x + coeff_y_prev * y_prev

    return y


def moving_average_convergence_divergence(
    x: np.ndarray, y_prev: np.ndarray, N_short: int, N_long: int
) -> np.ndarray:
    """MACD: Moving Average Convergence/Divergence

    From the paper:
    "Moving Average Convergence Divergence filter preprocessing for
    real-time event-related peak activity onset detection:
    application to fNIRS signals"

    Equations:
    MACD(x_t) = EMA_short(x_t) - EMA_long(x_t)

    Arguments:
    ----------
    x: raw signal input at time t
    y_prev: filtered signal at time t-1
    N_short: parameter 1 = how many time samples to use for moving average
    N_long: parameter 2 for long trend

    Returns:
    ----------
    y: filtered signal at time t
    """

    ema_short = exponential_moving_average(x=x, y_prev=y_prev, N=N_short)
    ema_long = exponential_moving_average(x=x, y_prev=y_prev, N=N_long)

    y = ema_short - ema_long

    return y


class CausalButterworth:
    """Causal Butterworth Filter

    Can be used for both processing all the samples and
    processing one sample (so that it can be combined)
    """

    # second-order sections
    sos: np.ndarray  # shape is [n_sections, 6], n_sections = ceil(order / 2)
    # initial conditions
    z: np.ndarray  # shape [n_sections, 2, n_ch]
    n_channels: int

    def __init__(
        self,
        first_time_sample: np.ndarray,
        cutoff: Union[float, list],
        sample_freq: float,
        btype: str = "pass",
        order: int = 4,
    ) -> None:
        """Initializing states for the filter

        first_time_sample:
            The very first time sample at t = 0
            If one channel, data[0]
            If multiple channels, data[0, :]
            (given data = [time x channel])
        cutoff:
            if 'high' or 'low' pass, float
            if 'pass' or 'stop', List[float, float]
        sample_freq:
            sample frequency of the signal in Hz
        btype:
            type of filter.
            Options: ['high', 'low', 'pass', 'stop']
        order:
            filter order.
            Note that this is IIR.
            Use second-order sections and sosfilt for stability.
            Note that the filter delay increases with filter order.
        """

        self.sos = butter_sos(cutoff, sample_freq, btype, order)
        zi = sosfilt_zi(self.sos)  # shape = [n_sections, 2]
        if first_time_sample.ndim == 0:
            self.n_channels = 1
        elif first_time_sample.ndim <= 2:
            self.n_channels = first_time_sample.reshape((1, -1)).shape[1]
        else:
            raise RuntimeError("first_time_sample.ndim > 2")
        self.z = np.tile(zi[:, :, None], (1, 1, self.n_channels))
        self.z = self.z * first_time_sample  # shape = [n_sections, 2, n_ch]

    def process_sample(self, sample: np.ndarray) -> np.ndarray:
        """Process sample causally

        This is so that you can combine with other process
        per sample. (e.g. Log -> HbO/HbR -> this in one sample)

        sample: np.ndarray, assume to be a vector of shape [n_time, n_channel]
            If n_dim is 1, assume to be [1, n_channel] sample

        ============ Ex. usage ===========
        # Prepare data
        fs = 100  # sampling frequency in Hz
        duration_short = 1.0  # signal duration is 1 second
        t_short = np.arange(0, duration_short, 1.0 / fs)
        test_freq_short = [5, 25, 45]
        data_short = np.hstack(
            [
                np.cos(2 * np.pi * f * t_short).reshape([-1, 1])
                for f in test_freq_short
            ]
        )  # data_short.shape = (100, 3)

        # Filtering one channel only
        cur_data = data_short[:, 0]
        cb = CausalButterworth(
            first_time_sample=cur_data[0],
            cutoff=7,
            sample_freq=fs,
            btype='high'
        )
        results = []
        # Process each sample causally
        for i in range(len(data_short)):
            results.append(cb.process_sample(sample=cur_data[i]))
        results_np = np.vstack(results)

        ===== Multiple channels case =====
        cb = CausalButterworth(
            first_time_sample=data_short[0, :],  # all channels
            cutoff=7,
            sample_freq=fs,
            btype='high'
        )
        results = []
        # Process each sample causally
        for i in range(data_short.shape[0]):
            results.append(cb.process_sample(sample=data_short[i, :]))
        results_np = np.vstack(results)
        """
        sample = np.asarray(sample)
        if sample.ndim == 0 and self.n_channels != 1:
            raise RuntimeError(
                f"Expected {self.n_channels} channels data, got 1 channel data"
            )
        # reshape for ndim==0 and ndim==1
        sample = sample.reshape((1, -1))

        if sample.shape[1] != self.n_channels:
            raise RuntimeError(
                f"Expected {self.n_channels} channels sample, received {sample.shape[1]} channel sample"
            )
        output, self.z = sosfilt(self.sos, sample, axis=0, zi=self.z)
        return output
