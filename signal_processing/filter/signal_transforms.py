#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

from typing import Tuple, Optional

import numpy as np
from scipy.fftpack import fft, fftfreq, fftshift
from scipy.signal import sosfilt, unit_impulse, lfilter


def do_fft(
    x: np.ndarray,
    dt: float,
    axis: int = -1,
    dB: bool = False,
) -> Tuple[np.ndarray, np.ndarray]:
    """Perform vanilla fft given then time-domain signal x and sampling time dt.

    Args:
    -----------
    x: np.ndarray, data to perform fft on

    dt: float, sampling time of the signal in seconds

    axis: int, axis along wich to perform fft. Each sample along this axis is
        considered to be sampled with dt

    dB: bool, flag to indicate whether the outputs will be returned in dB.

    Returns:
    --------
    xf: np.ndarray, gives the two-sided frequency values for the fft.

    xFFT: np.ndarray, same shape as x, giving the magnitude of the fft
        coefficients. If `dB`=True, then the result is `20*np.log10(xFFT)`
    """

    x_dims = x.shape
    N = x_dims[axis]
    xf = fftfreq(N) / dt
    x_fft = fft(x, axis=axis)
    xFFT = 1.0 / N * np.abs(x_fft)

    # move the values around so frequencies is from negative to positive
    xf = fftshift(xf)
    xFFT = fftshift(xFFT, axes=(axis,))

    if dB:
        xFFT = 20 * np.log10(xFFT)

    return xf, xFFT


def omega_to_f(omega: np.ndarray, fs: float) -> np.ndarray:
    """
    Convert normalized frequency in radians/sample to frequency in Hz
    """
    return fs * omega / (2 * np.pi)


def f_to_omega(f: np.ndarray, fs: float) -> np.ndarray:
    """
    Convert frequency in Hz to normalized frequncy in radians/sample
    """
    return f / fs * 2 * np.pi


def filter_impulse_response(
    sos_or_fir_coef: np.ndarray,
    N: int = 2048,
    fs: float = None,
    sos: bool = True,
) -> Tuple[np.ndarray, Optional[np.ndarray]]:
    """
    Given a filter specification in second order sections (sos),
    return the impulse response.

    Inputs:
    - sos_or_fir_coef: np.ndarray, second order section of iir filter or fir_coef of a
        FIR filter.
    - N: int, number of samples to calculate for the impulse response
    - fs: float, sampling rate in Hz. If not None, will return the time in seconds
        corresponding to the samples.
    - sos: bool. If true, assume `sos_or_fir_coef` is sos, otherwise as fir_coef

    Output:
    - response: np.ndarray, impulse response values. By default, the time unit
        is in samples.
    - time: np.ndarray, if fs is not None, return the time in seconds.
    """
    if sos:
        response = sosfilt(sos_or_fir_coef, unit_impulse(N))
    else:
        response = lfilter(b=sos_or_fir_coef, a=1, x=unit_impulse(N))
    if fs is not None:
        time = np.arange(N) / fs
        return response, time
    else:
        return response


def filter_freq_response(
    sos: np.ndarray, N: int = 2048, fs: float = None
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Given filter specification in second order sections (sos),
    return the frequency response by taking FFT of the impulse
    response.

    Inputs:
    - sos: np.ndarray, second order section of filter
    - N: int, number of samples to calculate for the impulse and frequency response
    - fs: float, sampling rate in Hz. If not None, will return the frequency in Hz,
        otherwise normalized frequency will be returned.

    Output:
    - frequency: np.ndarray, frequency of the frequency response. If fs is None,
        unit will be in radians/sample (ranging from 0 to np.pi),
        otherwise will be in Hz (ranging from 0 to fs / 2).
    - magnitude: np.ndarray, magnitude of filter
    - phase: np.ndarray, phase repsonse of filter, unit in radians.
    """
    impulse_response = filter_impulse_response(sos, N)

    # Get frequency response
    omega = (fftfreq(N) * 2 * np.pi)[0 : N // 2]
    freq_response = fft(impulse_response)[0 : N // 2]
    magnitude = np.abs(freq_response)
    phase = np.angle(freq_response)

    if fs is not None:
        freq = omega_to_f(omega, fs)
        return freq, magnitude, phase
    else:
        return omega, magnitude, phase


def filter_phase_delay(
    sos: np.ndarray, N: int = 2048, fs: float = None
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Given filter spec in second order sections of an IIR filter, return
    phase delay in samples, extracted from the phase response

    Note for FIR filters, phase delay is constant and equal to either
    (D/2) or (D-1)/2, where D is the number of coefficients in the filter.

    Inputs:
    - sos: np.ndarray, second order section of filter
    - N: int, number of samples to calculate for the impulse and frequency response
    - fs: float, sampling rate in Hz. If not None, will return the frequency in Hz,
        otherwise normalized frequency will be returned.

    Output:
    - frequency: np.ndarray, frequency of the frequency response. If fs is None,
        unit will be in radians/sample (ranging from 0 to np.pi),
        otherwise will be in Hz (ranging from 0 to fs / 2).
    - phase_delay: np.ndarray, phase delay of filter as function of frequency, unit
        is in samples.
    """
    omega, _, phase = filter_freq_response(sos, N)
    phase_delay = -phase / omega
    if fs is not None:
        freq = omega_to_f(omega, fs)
        return freq, phase_delay
    else:
        return omega, phase_delay


def filter_group_delay(
    sos_or_fir_coef: np.ndarray,
    N: int = 2048,
    fs: float = None,
    sos: bool = True,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Given filter spec in second order sections or (num, den) form, return group delay.
    Uses method in [1], which is cited by `scipy.signal.group_delay` but incorrectly implemented.

    Inputs:
    - sos_or_fir_coef: np.ndarray, second order section of iir filter or fir_coef of a
        FIR filter.
    - N: int, number of samples to calculate for the impulse and frequency response
    - fs: float, sampling rate in Hz. If not None, will return the frequency in Hz,
        otherwise normalized frequency will be returned.
    - sos: bool. If true, assume `sos_or_fir_coef` is sos, otherwise as fir_coef

    Output:
    - frequency: np.ndarray, frequency of the frequency response. If fs is None,
        unit will be in radians/sample (ranging from 0 to np.pi),
        otherwise will be in Hz (ranging from 0 to fs / 2).
    - group_delay: np.ndarray, group delay of filter as function of frequency, unit
        is in samples.

    [1] Richard G. Lyons, "Understanding Digital Signal Processing, 3rd edition", p. 830.
    """

    impulse_response = filter_impulse_response(sos_or_fir_coef, N, sos=sos)
    k = np.arange(N)
    fft_gd = np.real(fft(k * impulse_response) / fft(impulse_response))[0 : N // 2]
    omega = (fftfreq(N) * 2 * np.pi)[0 : N // 2]
    if fs is not None:
        freq = omega_to_f(omega, fs)[0 : N // 2]
        return freq, fft_gd
    else:
        return omega, fft_gd
