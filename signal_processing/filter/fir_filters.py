#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

from typing import Tuple, Union

import numpy as np
from scipy.signal import firwin, lfilter_zi, lfilter


def fir_coefficients_states(
    cutoff: Union[float, list], fs: float, btype: bool, order: int
) -> Tuple[np.ndarray, np.ndarray]:
    """Real-time equivalent FIR filter returning coefficients

    Args:
    ----------
    cutoff: float or list
        cutoff frequency to be specified
        e.g. cutoff = 3  # Hz
        when using bandpass or bandstop, pass list
        e.g. [0.01, 3]  = 0.01 Hz - 3 Hz

    fs: float
        sampling frequency

    btype: bool
        [default = True (lowpass). False = highpass]
        In scipy 1.3.0 or above, the following can be used [TODO]
        Options: ‘bandpass’, ‘lowpass’, ‘highpass’, ‘bandstop’
        Equivalent to btype in iir_filter

    order: int
        filter order

    Returns:
    ----------
    b: np.ndarray
        coefficients of length num_taps FIR filter

    z: np.ndarray
        the initial state for the filter

    Example of real-time emulation:
    ----------
    # Get coefficients and initial state
    b, z = fir_coefficients_states(cutoff=cutoff,
                                   fs=fs,
                                   btype='lowpass',
                                   order=order)
    # Initialize
    filtered = np.zeros(data.size)
    # Sample by sample
    for i, x in enumerate(data):
        filtered[i], z = lfilter(b, 1, [x], zi = z)
    """

    # Calculate the nyquist frequency
    nyquist = fs / 2.0
    # Normalize the cutoff frequency using nyquist
    normalized_cutoff = np.array(cutoff) / nyquist
    # Design coefficients of length numtaps for FIR filter
    b = firwin(numtaps=order, cutoff=normalized_cutoff, pass_zero=btype)
    # Compute initial steady state of step response
    z = lfilter_zi(b, 1)

    return b, z


def fir_filter(
    data: np.ndarray,
    cutoff: float,
    fs: float,
    btype: bool = True,
    order: int = 50,
    axis: int = -1,
) -> np.ndarray:
    """FIR filtering returning filtered signal,
    The filtered output will start at the same initial value as the input signal
    by matching initial conditions.

    Note despite matching initial condition through the use of `lfilter_zi`, the
    first few samples of the output signal will not be simply a delayed version.
    The number of weird samples scale with the filter order.

    Args:
    ----------
    data: np.ndarray
        data to be filtered

    cutoff: float
        cutoff frequency to be specified
        e.g. cutoff = 3  # Hz

    fs: float
        sampling frequency

    btype: bool
        [default = True (lowpass). False = highpass]
        In scipy 1.3.0 or above, the following can be used [TODO]
        Options: ‘bandpass’, ‘lowpass’, ‘highpass’, ‘bandstop’
        Default: 'lowpass'
        Equivalent to btype in iir

    order: int
        filter order

    axis: int, dimension along which to apply the filter, same as that for `lfilter`
        default is -1

    Returns:
    ----------
    filtered: np.ndarray
        filtered data, same shape as data
    """

    # Get coefficients and initial state
    b, z = fir_coefficients_states(cutoff=cutoff, fs=fs, btype=btype, order=order)
    x_dims = data.shape

    # if multi-dimensional array, have to modify initial condition z
    # to fit the dimension of the input data
    if len(x_dims) > 1:
        z_dims = np.ones(len(x_dims), dtype=int)
        z_dims[axis] = -1
        z = z.reshape(z_dims)  # convert to row vector
        tile_dims = np.array(x_dims)
        tile_dims[axis] = 1
        z = np.tile(z, tile_dims)

    filtered, _ = lfilter(b, 1, data, zi=z, axis=axis)

    return filtered


def check_symmetry(h: np.ndarray) -> bool:
    """
    Given FIR filter coefficients `h`, check if it's symmetric
    or antisymmetric
    """
    N = len(h)
    symmetry = all(np.isclose(h[k], h[N - k - 1]) for k in range(N))
    antisymmetry = all(np.isclose(h[k], -h[N - k - 1]) for k in range(N))
    if symmetry or antisymmetry:
        return True
    return False


def symmetric_fir_group_delay(h: np.ndarray) -> int:
    """
    Group delay for symmetric or antisymmetric FIR filters is about
    half of the filter length.

    If not symmetric, use `.signal_transforms.filter_group_delay` instead
    """
    if not check_symmetry(h):
        raise RuntimeError("FIR filter is not symmetric or antisymmetric!")
    N = len(h)
    if N % 2 == 1:
        return (N - 1) // 2
    else:
        return N // 2
