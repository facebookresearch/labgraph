#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

import unittest

import numpy as np
from colorednoise import powerlaw_psd_gaussian
from ..dummy_generator import (
    _make_time_index,
    dummy_physiological_noise,
    motion_noise,
    simulated_hemodynamics,
)
from mne.time_frequency import psd_array_multitaper
from scipy.signal import savgol_filter


class DummyGeneratorTest(unittest.TestCase):
    def setUp(self):
        np.random.seed(42)

    def test_time_index(self):

        with self.assertRaises(RuntimeError):
            _make_time_index(0.001, 100)

        time_index = _make_time_index(1, 1000)

        self.assertTrue(np.allclose(time_index, np.arange(0, 1, 0.001)))

        time_index = _make_time_index(5, 50)
        self.assertEqual(time_index.shape[0], 50 * 5)

    def test_consistent_behavior(self):
        # duration and sample_rate should work the same way in all the generators

        sample_rate = 50
        duration = 1
        n_samples = duration * sample_rate
        sim_Hb = simulated_hemodynamics(
            amplitude=1, sample_rate=sample_rate, duration=duration
        )

        physio_noise = dummy_physiological_noise(
            amplitude=4e-7,
            sample_rate=sample_rate,
            interest_freq=1,
            phase=np.pi / 4,
            duration=duration,
        )

        measurement_noise = powerlaw_psd_gaussian(exponent=1.0, size=n_samples)

        self.assertEqual(sim_Hb.shape, physio_noise.shape)
        self.assertEqual(sim_Hb.shape, measurement_noise.shape)

    def test_sim_hemodynamics(self):
        duration = 30
        sample_rate = 50

        # Create simulated hemodynamics

        sim_Hb1 = simulated_hemodynamics(
            amplitude=1, sample_rate=sample_rate, duration=duration
        )

        sim_Hb2 = simulated_hemodynamics(
            amplitude=1, sample_rate=sample_rate * 2, duration=duration
        )

        # check that peak is basically 5s
        ts1 = _make_time_index(duration, sample_rate)
        ts2 = _make_time_index(duration, sample_rate * 2)
        self.assertAlmostEqual(np.abs(ts1[np.argmax(sim_Hb1)] - 5.0), 0)
        self.assertAlmostEqual(np.abs(ts2[np.argmax(sim_Hb2)] - 5.0), 0)

    def test_physiological_noise(self):
        duration = 1
        sample_rate = 1000
        interest_freq = 1

        sim_Hb = simulated_hemodynamics(
            amplitude=1, sample_rate=sample_rate, duration=duration
        )
        # Simulated cardiac noise
        cardiac_wave = dummy_physiological_noise(
            amplitude=4e-7,
            sample_rate=sample_rate,
            interest_freq=interest_freq,
            phase=np.pi / 4,
            duration=duration,
        )
        # Check dimensions
        self.assertEqual(sim_Hb.shape, cardiac_wave.shape)

        # Calculate the PSD and make sure the peak is in 1 Hz
        # calculate multitaper PSD
        psds, freqs = psd_array_multitaper(cardiac_wave, sample_rate, n_jobs=12)
        power_log10 = np.log10(psds)
        ind_of_peak = np.unravel_index(
            np.argmax(power_log10, axis=None), power_log10.shape
        )[0]
        self.assertAlmostEqual(freqs[ind_of_peak], interest_freq)

        cardiac_wave_double_freq = dummy_physiological_noise(
            amplitude=4e-7,
            sample_rate=sample_rate * 2,
            interest_freq=interest_freq,
            phase=np.pi / 4,
            duration=duration,
        )

        self.assertTrue(np.allclose(cardiac_wave, cardiac_wave_double_freq[::2]))

    def test_pink_noise(self):
        beta = 1
        sample_rate = 500
        duration = 2
        n_samples = duration * sample_rate
        y = powerlaw_psd_gaussian(exponent=beta, size=n_samples)
        # calculate the PSD
        psds, freqs = psd_array_multitaper(y, sample_rate, n_jobs=12)

        # after enough smoothing on PSD,
        # pink noise should follow smooth 1/f curve
        # thus low freq power > high freq power
        psds_smooth = savgol_filter(psds, 101, 3)
        low_freq_power = np.median(psds_smooth[:10])
        med_freq_power = np.median(psds_smooth[80:110])
        high_freq_power = np.median(psds_smooth[400:])
        self.assertGreaterEqual(low_freq_power, med_freq_power)
        self.assertGreaterEqual(med_freq_power, high_freq_power)

        # make sure behavior is same if we change sampling frequency
        # TODO: make this a slightly more robust test
        y_double_freq = powerlaw_psd_gaussian(exponent=beta, size=2 * n_samples)
        psds, freqs = psd_array_multitaper(y_double_freq, sample_rate, n_jobs=12)

        psds_smooth = savgol_filter(psds, 101, 3)
        low_freq_power = np.median(psds_smooth[:10])
        med_freq_power = np.median(psds_smooth[80:110])
        high_freq_power = np.median(psds_smooth[400:])
        self.assertGreaterEqual(low_freq_power, med_freq_power)
        self.assertGreaterEqual(med_freq_power, high_freq_power)

    def test_motion_noise(self):
        duration = 20
        sample_rate = 5000

        # this conveniently checks that we don't throw if duration
        # exceeds window ize
        noise = motion_noise(
            motion_amplitude=3,
            motion_duration_mean=0.5,
            sample_rate=sample_rate,
            sample_duration=duration,
        )

        # the nonzero (noise) part should have slope \approx motion_amplitude
        # but this is not a tight test since we get a random chunk
        nonzero = noise[noise > 0]
        slope = (nonzero[-1] - nonzero[0]) / len(nonzero) * sample_rate
        self.assertAlmostEqual(slope, 3.0, places=2)

        sample_rate = 150
        noise = motion_noise(
            motion_amplitude=1.75,
            motion_duration_mean=0.5,
            sample_rate=sample_rate,
            sample_duration=duration,
        )

        nonzero = noise[noise > 0]
        slope = (nonzero[-1] - nonzero[0]) / len(nonzero) * sample_rate
        self.assertAlmostEqual(slope, 1.75, places=2)
