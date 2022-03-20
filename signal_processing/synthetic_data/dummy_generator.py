#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

import logging

import numpy as np
import scipy.stats

# colored noise related
from numpy import sqrt, newaxis
from numpy import sum as npsum
from numpy.fft import irfft, rfftfreq
from numpy.random import normal
from scipy.stats import truncnorm


def _make_time_index(duration: float, sample_rate: float) -> np.ndarray:
    """makes indices for a time series of given duration (in s)
    and sample rate (in hz)
    """
    if duration < 1 / sample_rate:
        raise RuntimeError(
            f"sample rate {sample_rate}\
                            too slow for duration {duration}!"
        )
    return np.arange(0, duration, 1 / sample_rate)


def gamma_shape_rate(x: np.ndarray, shape: float, rate: float) -> np.ndarray:
    """
    scipy.stats.gamma is parameterized by shape and scale=1/rate,
    we flip this for convenience
    """
    scale = 1 / rate
    return scipy.stats.gamma.pdf(x, a=shape, scale=scale)


def double_gamma_hrf(
    t: float,
    A: float,
    alpha1: float = 6.0,
    alpha2: float = 16.0,
    beta1: float = 1,
    beta2: float = 1,
    c: float = 1 / 6,
) -> np.ndarray:
    """
    HRF as linear combination of two gamma distributions
    Default parameters match:
     https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3318970/#FD7
    """
    return A * (
        gamma_shape_rate(t, alpha1, beta1) - c * gamma_shape_rate(t, alpha2, beta2)
    )


def simulated_hemodynamics(
    amplitude: float, duration: float, sample_rate: float, pad_len: int = 0
) -> np.ndarray:
    """Generate simulated hemodynamics

    Generate simulated hemodynamics using double-gamma HRF over
    a particular window and sample rate

    Attributes:
    ----------
    pad_len: int
        how many samples to shift the HRF
        [Default = 0]
        e.g. pad_len = 50
             shift the HRF start by 50 samples
    """
    ts = _make_time_index(duration, sample_rate)
    # canonical HRF is in seconds
    hrf = double_gamma_hrf(ts, amplitude)
    # shift the initiation point
    # only left padding to shift with constant 0
    if int(duration * sample_rate) == 0:
        logging.warning(
            "Your int(duration * sample_rate) is zero. \
                          Returned array will be empty."
        )
    if pad_len > int(duration * sample_rate):
        logging.warning(
            "Your pad_len is larger than the whole data. \
                          Returned array will be all zeros."
        )
    hrf = np.pad(hrf, (pad_len, 0), "constant")[: int(duration * sample_rate)]

    return hrf


def dummy_physiological_noise(
    amplitude: float,
    sample_rate: float,
    interest_freq: float,
    phase: float,
    duration: float,
) -> np.ndarray:
    """Generate dummy physiological noise

    Attributes:
    ----------
    amplitude: float
        controls the amplitude of the dummy signal
    sample_rate: float
        sampling frequency
    interest_freq: float
        which frequency to generate the signal on
        e.g. sample_rate = 5 and interest_freq = 1
             means the sampling frequency is 5 Hz
             but the dominant power exists as 1 Hz
    phase: float
        phase of the signal
    duration: float
        duration of signal

    Returns:
    ----------
    dummy_noise: np.ndarray
        generated dummy signal

    References:
    ----------
    Nguyen et. al. 2018: "Adaptive filtering of
                          physiological noises in fNIRS data"
    Scarpa et. al. 2013: "A reference-channel based methodology
                          to improve estimation of event-related
                          hemodynamic response from fNIRS measurements"
                          Equation (4)
    """

    ts = _make_time_index(duration, sample_rate)

    dummy_noise = amplitude * np.sin(2 * np.pi * interest_freq * ts + phase)

    return dummy_noise


def motion_noise(
    motion_amplitude: float,
    motion_duration_mean: float,
    sample_rate: float,
    sample_duration: float,
) -> np.ndarray:
    """
    Best guess of motor drift from Scarpa et al. 2013
    Attributes:
    ----------
    motion_amplitude: float
        slope of the motion drift
    motion_duration_mean: float
        mean duration of motion
    sample_rate: float
        sampling frequency
    duration: float
        duration of signal

    Returns:
    ----------
    dummy_noise: np.ndarray
        generated dummy signal
    Notes:
    --------
    from Scarpa et al 2013:
    "In order to simulate artifacts (e.g., due to movements of the participant or
    shifts of a source or a detector) short non-cyclic abrupt drifts were added in
     6 out of30 par- ticipants (it is the typical fraction noticed in our
     experiment), at a random temporal position and with random amplitude,
     and is repre- sented by the noise term r(t), different channel by channel.

    this is super vague, but just so we have an implementation:
    - let's pretend "non cyclic abrupt drift" is a linear trend with some slope
    - let's pretend "random temporal position" is interval based on
        uniform start and truncated normal duration (truncated at 0)
        with parametric mean and constant coeff of variation=1"

    References:
    ----------
    Scarpa et. al. 2013: "A reference-channel based methodology
                          to improve estimation of event-related
                          hemodynamic response from fNIRS measurements"
                          p.109

    """
    times = _make_time_index(sample_duration, sample_rate)
    motion_start = np.random.randint(low=0, high=len(times))

    # duration with constant coeff of variation
    motion_duration = truncnorm.rvs(
        loc=motion_duration_mean * sample_rate,
        scale=motion_duration_mean * sample_rate,
        a=0,
        b=np.inf,
    )

    motion_times = _make_time_index(motion_duration, sample_rate)

    # in case we picked a motion duration greater than the window length,
    # it's still valid, but we truncate
    motion_times = motion_times[
        : min(motion_start + len(motion_times), len(times) - motion_start)
    ]

    noise = motion_times * motion_amplitude
    out = np.zeros_like(times)
    out[motion_start : (motion_start + len(motion_times))] = noise
    return out
