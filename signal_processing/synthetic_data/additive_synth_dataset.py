#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

from typing import List, Optional, Tuple, Union

import numpy as np
from colorednoise import powerlaw_psd_gaussian
from .dummy_generator import (
    dummy_physiological_noise,
    motion_noise,
    simulated_hemodynamics,
)
from torch.utils.data import Dataset


class AdditiveSynthDataset(Dataset):
    """
    Generates a synthetic finger-tapping fNIRS dataset using the same
    additive noise model as:
    Scarpa, F., Brigadoi, S., Cutini, S., Scatturin, P., Zorzi, M.,
     Dell’Acqua, R., & Sparacino, G. (2013). A reference-channel based
     methodology to improve estimation of event-related hemodynamic
     response from fNIRS measurements.
     NeuroImage, 72, 106–119. https://doi.org/10.1016/j.neuroimage.2013.01.021

    Default parameters are as best as we could match that paper, but the paper
    was ambiguous in many ways, so no guarantees.
    """

    def __init__(
        self,
        n_trials: int,
        trial_length: float,
        channel_dists: np.ndarray,
        class_proportions: Optional[List[float]] = None,
        sample_rate: int = 5,
    ):
        self.n_trials = n_trials
        self.trial_length = trial_length
        self.channel_dists = channel_dists
        self.n_channels = len(channel_dists)
        self.sample_rate = sample_rate
        self.trial_samples = int(trial_length * sample_rate)

        if class_proportions is None:
            class_proportions = [1 / 3] * 3

        self.labels = np.random.choice(
            np.arange(len(class_proportions)),
            size=n_trials,
            replace=True,
            p=class_proportions,
        )

        self.X = np.zeros((n_trials, self.n_channels, self.trial_samples))

        hrf_scales = self.hrf_scale_from_channel_dists(channel_dists)

        for trial in range(n_trials):
            for channel, hrf_scale in enumerate(hrf_scales):
                # HACK: fragile: assume label 0 means no HRF,
                # label 1 means left and left is first half of channels,
                # label 2 means right and right is 2nd half of channels,
                # otherwise 0
                if (
                    self.labels[trial] == 0
                    or (self.labels[trial] == 1 and channel > (self.n_channels // 2))
                    or (self.labels[trial] == 2 and channel <= (self.n_channels // 2))
                ):
                    hrf_scale = 0

                self.X[trial, channel, :] = self.generate_synth_data(hrf_scale)

    def hrf_scale_from_channel_dists(self, channel_dists: np.ndarray) -> np.ndarray:
        """
        hrf weight (k in the paper) is a function of channel dists,
        if we follow the original paper
        there's 2 cutoffs and k is 0 for surface/close dists, 0.5 for "medium"
        dists, and 1.0 for "long"/deep dists
        they don'ts ay what "medium" dists are but elsewhere in the paper
        they say distances above 1.5cm but below 3cm are too
        short to be standard channel but aren't reference channels, so we assume
        those are "medium".
        """

        hrf_scale = np.zeros_like(channel_dists)
        hrf_scale[channel_dists > 15] = 0.5
        # distances 3cm or above are standard channels
        hrf_scale[channel_dists >= 30] = 1.0
        return hrf_scale

    def __len__(self) -> int:
        return self.n_trials

    def __getitem__(self, index: Union[int, slice]) -> Tuple[np.ndarray, np.ndarray]:
        return self.X[index, ...], self.labels[index]

    def sim_physio_noise(
        self,
        frequencies_mean: Optional[List[float]] = None,
        frequencies_sd: Optional[List[float]] = None,
        amplitudes_mean: Optional[List[float]] = None,
        amplitudes_sd: Optional[List[float]] = None,
    ) -> np.ndarray:
        """
        Physiological noise
        Per paper table 1, there are 5 components:
        very low freq, low freq, vasomotor, respiratory, cardiac (given in
        defaults)
        """
        if frequencies_mean is None:
            frequencies_mean = [0.002, 0.01, 0.07, 0.2, 1.1]
        if frequencies_sd is None:
            frequencies_sd = [0.0001, 0.001, 0.04, 0.03, 0.1]
        if amplitudes_mean is None:
            amplitudes_mean = [700, 700, 400, 200, 400]
        if amplitudes_sd is None:
            amplitudes_sd = [100, 100, 10, 10, 10]

        physio_noises = [
            dummy_physiological_noise(
                amplitude=np.random.normal(a_mean, a_sd),
                sample_rate=self.sample_rate,
                interest_freq=np.random.normal(f_mean, f_sd),
                phase=np.random.normal() * 2 * np.pi,
                duration=self.trial_length,
            )
            for f_mean, f_sd, a_mean, a_sd in zip(
                frequencies_mean, frequencies_sd, amplitudes_mean, amplitudes_sd
            )
        ]

        return np.sum(np.stack(physio_noises), axis=0)

    def generate_measurement_noise(
        self,
        exponent: float = 0,
        amplitude: float = 400,
        sd: float = 180,
        fmin: float = 1,
    ) -> np.ndarray:
        """
        white noise in original paper, amplitude in the paper is 400 ± 180,
        TODO: mean and sd doesn't really make sense for non-white noise
        """
        eta = powerlaw_psd_gaussian(
            exponent=exponent,
            size=self.trial_length * self.sample_rate,
            fmin=fmin,
        )

        return eta / np.mean(eta) * sd + amplitude

    def generate_hrf(
        self, hrf_scale: float = 1, amplitude: float = 420.0
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
        source/detector pairs to have hrf_scale=0, saturating to hrf_scale=1.
        """

        u_true = hrf_scale * simulated_hemodynamics(
            amplitude=amplitude,
            sample_rate=self.sample_rate,
            duration=self.trial_length,
        )
        return u_true

    def generate_motion_noise(self) -> np.ndarray:
        """
        No idea what motion params are?
        """
        return motion_noise(
            motion_amplitude=500,
            motion_duration_mean=0.5,
            sample_rate=self.sample_rate,
            sample_duration=self.trial_length,
        )

    def generate_synth_data(self, hrf_scale: float = 1) -> np.ndarray:
        """
        y(t) = hrf_scale * u_true(t) + \\phi_sim(t) + \\eta(t) + r(t), where:
        - hrf_scale is a scaling coefficient based on depth
          (in the original paper this is 0 for ref channels,
          1 for signal channels, and 0.5 for some other "standard channels")
        - u_true(t) is the true HRF, made by simulated_hemodynamics()
        - \\phi_sim(t) is the physiological noise, made from sim_physio_noise()
        - \\eta(t) is "random" or white noise
        - r(t) is motion noise
        """

        phi_sim = self.sim_physio_noise()
        u_true = self.generate_hrf(hrf_scale)
        measurement_noise = self.generate_measurement_noise()
        motion_noise = self.generate_motion_noise()
        return u_true + phi_sim + measurement_noise + motion_noise
