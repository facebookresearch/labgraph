#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

import random
from typing import List, Optional, Tuple, Union

import numpy as np
from colorednoise import powerlaw_psd_gaussian
from ..utils.doc.docfill import fill_in_docstring
from .dummy_generator import (
    dummy_physiological_noise,
    simulated_hemodynamics,
)
from scipy import signal

###############################################################################
#                    Documentation for Synthesized Data                       #
###############################################################################
_common_docs = fill_in_docstring(
    {
        "n_trials": """channel_data : int
        Number of trials in the experiment including all conditions.
        """,
        "trial_length": """trial_length : float
        Length of each trial in seconds
        """,
        "class_labels": """class_labels: List[str]
        class_labels is a list of strings defining the labels or conditions
        """,
        "channel_dists": """channel_dists :  np.ndarray
        SD distance array for all channels
        """,
        "hrf_scale_for_cond": """ hrf_scale_for_cond : np.ndarray [n_channels, n_conds]
        hrf_scale_for_condition to scale the data based on condition.
        n_channels is the number of channels
        n_conds is the the number of conditions or class_labels
        details.
        """,
        "sample_rate": """ sample_rate : float
        Sampling frequency of acquisition in Hz
        """,
    }
)


@_common_docs
class AdditiveSynthDatasetVariant(object):
    """
    based on the combining the ideas of 2 papers
    1. Scholkmann F, Spichtig S, Muehlemann T, Wolf M.
    How to detect and reduce movement artifacts in near-infrared imaging
    using moving standard deviation and spline interpolation.
    Physiol Meas. 2010 May;31(5):649-62.
    doi: 10.1088/0967-3334/31/5/004. Epub 2010 Mar 22. PMID: 20308772. (Default is this one)

    2. Scarpa, F., Brigadoi, S., Cutini, S., Scatturin, P., Zorzi, M.,
     Dell’Acqua, R., & Sparacino, G. (2013). A reference-channel based
     methodology to improve estimation of event-related hemodynamic
     response from fNIRS measurements.
     NeuroImage, 72, 106–119. https://doi.org/10.1016/j.neuroimage.2013.01.021

    """

    def __init__(
        self,
        n_trials: int,
        trial_length: float,
        channel_dists: np.ndarray,
        class_labels: List[str],
        hrf_scale_for_cond: np.ndarray,
        sample_rate: float = 10.0,
    ):
        self.n_trials = n_trials
        self.trial_length = trial_length
        self.channel_dists = channel_dists
        self.n_channels = len(channel_dists)
        self.sample_rate = sample_rate
        self.trial_samples = int(trial_length * sample_rate)
        self.labels = class_labels

        self.X = np.zeros((n_trials, self.n_channels, self.trial_samples))

        hrf_scales_from_distance = hrf_scale_from_channel_dists(channel_dists)

        for trial in range(n_trials):
            for label in range(len(class_labels)):
                for channel, hrf_scale_from_distance in enumerate(
                    hrf_scales_from_distance
                ):
                    hrf_scale_final = (
                        hrf_scale_from_distance * hrf_scale_for_cond[channel, label]
                    )

                    self.X[trial, channel, :] = generate_synth_data(
                        hrf_scale_final, self.sample_rate, self.trial_length
                    )

    def __len__(self) -> int:
        return self.n_trials

    def __getitem__(self, index: Union[int, slice]) -> Tuple[np.ndarray, np.ndarray]:
        return self.X[index, ...], self.labels[index]


def hrf_scale_from_channel_dists(channel_dists: np.ndarray) -> np.ndarray:
    """
    Assuming hrf_scales would attenuate linearly with SD distance
    """

    hrf_scale = np.zeros_like(channel_dists)
    hrf_scale[np.array(channel_dists) < 10] = 0.5
    hrf_scale[np.array(channel_dists) >= 10] = 1.00
    hrf_scale[np.array(channel_dists) >= 20] = 0.50
    hrf_scale[np.array(channel_dists) >= 30] = 0.33
    hrf_scale[np.array(channel_dists) >= 40] = 0.25
    hrf_scale[np.array(channel_dists) >= 50] = 0.20
    hrf_scale[np.array(channel_dists) >= 60] = 0.16
    return hrf_scale


def sim_physio_noise(
    sample_rate: float,
    trial_length: float,
    frequencies_mean: Optional[List[float]] = None,
    frequencies_sd: Optional[List[float]] = None,
    amplitudes_mean: Optional[List[float]] = None,
    amplitudes_sd: Optional[List[float]] = None,
) -> np.ndarray:
    """
    Sample_rate in Hz and trial length in seconds
    from the paper Scholkmann et al, 2010
    The amplitude and frequency values of each sine wave were defined according to the mean frequencies of real NIRI signals

    very high frequency oscillation (heart rate, f = 1 Hz, µ = 0.6)
    high frequency oscillation (respiration, f = 0.25 Hz, µ = 0.2)
    low frequency oscillation (f = 0.1 Hz, µ = 0.9)
    very low frequency oscillation (f = 0.04 Hz, µ = 1).

    """
    if frequencies_mean is None:
        frequencies_mean = [0.002, 0.03, 0.1, 0.25, 1.1]
    if frequencies_sd is None:
        frequencies_sd = [0.0001, 0.01, 0.03, 0.05, 0.2]
    if amplitudes_mean is None:
        amplitudes_mean = [0.7, 0.9, 0.9, 0.2, 0.6]
    if amplitudes_sd is None:
        amplitudes_sd = [0.01, 0.01, 0.1, 0.1, 0.1]

    physio_noises = [
        dummy_physiological_noise(
            amplitude=np.random.normal(a_mean, a_sd),
            sample_rate=sample_rate,
            interest_freq=np.random.normal(f_mean, f_sd),
            phase=np.random.normal() * 2 * np.pi,
            duration=trial_length,
        )
        for f_mean, f_sd, a_mean, a_sd in zip(
            frequencies_mean, frequencies_sd, amplitudes_mean, amplitudes_sd
        )
    ]

    return np.sum(np.stack(physio_noises), axis=0)


def generate_measurement_noise(sample_rate: float, trial_length: float) -> np.ndarray:

    exponent = 1
    amplitude = 0.4
    sd = 0.018
    fmin = 0

    eta = powerlaw_psd_gaussian(
        exponent=exponent, size=int(trial_length * sample_rate), fmin=fmin
    )

    return eta / np.mean(eta) * sd + amplitude


def generate_hrf(
    hrf_scale: float, sample_rate: float, trial_length: float
) -> np.ndarray:
    """
    From the paper,
    "In order to simulate the HR due to two different
    stimuli and with shapes, amplitudes and latencies in
    agreement with previous findings regarding finger
    tapping tasks, two utrue profiles were generated
    by properly tuning the parameters in Eq. (2),
    allowing small variations in peak amplitude and
    latency between a trial and another. For HbO, this led to a
    first HR profile with a peak amplitude of 420±20 nM and a peak
    latency equal to 5.0±.2 s, while the second HR profile had a
    peak amplitude of 360±20 nM and a peak latency equal to 5.5±.2 s."
    So basically we have no idea what the parameters are.

    hrf_scale here is `k` in the paper. Eventually we may want very close
    source/detector pairs to have hrf_scale=0, saturating to hrf_scale=1
    on pairs.
    """
    amplitude = 1

    u_true = hrf_scale * simulated_hemodynamics(
        amplitude=amplitude, sample_rate=sample_rate, duration=trial_length
    )
    return u_true


def generate_motion_noise(sample_rate: float, trial_length: float) -> np.ndarray:
    """
    The better simulation of motion artifacts in Scholkmann et al, 2010 than Scarpa et al, 2013
    motivated to reproduce a variant of this paper
    Here Motion = Base Shift + pulse + temporary LF oscillation + Spike (spike added; not in original paper)

    """
    # Pulse
    """
    Simulating a pulse with values between [-4 4] and in the entire duration
    """
    duration = int(trial_length * sample_rate)
    pulse = np.zeros(duration)

    pulse[random.randint(1, int(len(pulse) / 3))] = random.randint(-4, 4)

    # Shift
    """
    Simulating a base shift with values between [-4 4] and in the 1/4th of entire duration
    """
    shift = np.zeros(duration)
    shift[
        random.randint(1, len(shift) // 4) : random.randint(
            len(shift) // 4, len(shift) // 2
        )
    ] = random.randint(-4, 4)

    # temporary LF oscillation
    """
    Not exactly clear what motion it corresponds to probably due to slouching or slow head movement
    Using a 10s Gaussian wave to define it
    """
    LFO = np.zeros(duration)
    start = len(LFO) // 4
    end = 3 * len(LFO) // 4
    LFO[start:end] = signal.gaussian(len(LFO) // 2, std=len(LFO) // 20)

    # spikes
    """
    Using a spikes 0f 2s duration, similar to head motion or body motion
    """
    spike = np.zeros(duration)

    loc, scale = random.randint(0, 1), random.randint(0, 1)
    s = np.random.laplace(loc, scale, 20)
    start = random.randint(1, len(spike) - 20)
    end = start + 20
    spike[start:end] = s

    """
    It returns motion for each trial. It is highly improbable that all types of motion are present within one trial.
    So returning a random combination of motions (including no motion for a trial)
    e.g. one trial can have no motion or no_motion+spikes
    """
    no_motion = np.zeros(duration)
    motions = [no_motion, pulse, shift, LFO, spike]
    motion = sum(motions[: random.randint(0, 5)])
    if isinstance(motion, list) and len(motion) == 0:
        return no_motion
    elif np.array(motion).size == 1:
        return no_motion
    else:
        return np.array(motion)


def generate_synth_data(
    hrf_scale: float, sample_rate: float, trial_length: float
) -> np.ndarray:
    """
    y(t) = hrf_scale * u_true(t) + \\phi_sim(t) + \\eta(t) + r(t), where:
        - u_true(t) is the true HRF, made by simulated_hemodynamics()
        - \\phi_sim(t) is the physiological noise, made from sim_physio_noise()
        - \\eta(t) is "random" or white noise
        - r(t) is motion noise
    """
    sample_rate = sample_rate
    trial_length = trial_length
    hrf_scale = hrf_scale

    phi_sim = sim_physio_noise(sample_rate, trial_length)

    u_true = generate_hrf(hrf_scale, sample_rate, trial_length)

    measurement_noise = generate_measurement_noise(sample_rate, trial_length)

    motion_noise = generate_motion_noise(sample_rate, trial_length)

    return u_true + phi_sim + measurement_noise + motion_noise
