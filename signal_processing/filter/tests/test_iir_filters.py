#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

import unittest
from functools import partial

import numpy as np
from ..iir_filters import (
    butterworth_filter,
    butterworth_sos_filter,
    exponential_moving_average,
    moving_average_convergence_divergence,
    CausalButterworth,
)
from ..signal_transforms import do_fft
from ...synthetic_data.dummy_generator import dummy_physiological_noise
from scipy.signal import find_peaks


# Use FFT to check attenuation of bandpass
# Use peak finding to check for delay
# Use narrow passband to check difference between filtfilt and sosfiltfilt
class InfiniteImpulseResponseFilterTest(unittest.TestCase):
    def setUp(self):
        # Initializing sampling parameters and signals

        self.fs = 100  # sampling frequency in Hz
        self.duration_short = 1.0  # signal duration is 1 second
        self.t_short = np.arange(0, self.duration_short, 1.0 / self.fs)

        self.duration_long = 1000.0
        self.t_long = np.arange(0, self.duration_long, 1.0 / self.fs)

        # Nyquist is fs/2 = 50Hz,
        # Create cosines of 5, 25, 45 Hz
        # Data is of dimension [n_samples, n_channel]
        # Nominal filtering data -- short duration
        self.test_freq_short = [5, 25, 45]
        self.data_short = np.hstack(
            [
                np.cos(2 * np.pi * f * self.t_short).reshape([-1, 1])
                for f in self.test_freq_short
            ]
        )

        # Use FFT for checking frequency attenuation
        xf, xFFT = do_fft(self.data_short, dt=1.0 / self.fs, axis=0, dB=False)
        self.freq_idx_short = np.hstack(
            [np.argmin(np.abs(xf - i)) for i in self.test_freq_short]
        )
        self.mag_short = np.diag(xFFT[self.freq_idx_short, :])
        print(f"magnitude for {self.test_freq_short} is {self.mag_short}")
        # Use peak finding to check zero-phase delay
        self.peaks_idx_short = [
            find_peaks(self.data_short[:, i], height=0.5)[0]
            for i in range(len(self.test_freq_short))
        ]

        # Create cosines of [0.01, 0.05, 0.1] Hz for testing filter stability
        # Low frequency, long duration
        self.test_freq_long = [0.01, 0.05, 0.1]
        self.data_long = np.hstack(
            [
                np.cos(2 * np.pi * f * self.t_long).reshape([-1, 1])
                for f in self.test_freq_long
            ]
        )

        # Use FFT for checking frequency attenuation
        xf, xFFT = do_fft(self.data_long, dt=1.0 / self.fs, axis=0, dB=False)
        self.freq_idx_long = np.hstack(
            [np.argmin(np.abs(xf - i)) for i in self.test_freq_long]
        )
        self.mag_long = np.diag(xFFT[self.freq_idx_long, :])

        # Use peak finding to check zero-phase delay
        self.peaks_idx_long = [
            find_peaks(self.data_long[:, i], height=0.5)[0]
            for i in range(len(self.test_freq_long))
        ]

        # Alias for the functions to test
        self.do_lfilter = partial(butterworth_filter, noDelay=False)
        self.do_filtfilt = partial(butterworth_filter, noDelay=True)
        self.do_sosfilt = partial(butterworth_sos_filter, noDelay=False)
        self.do_sosfiltfilt = partial(butterworth_sos_filter, noDelay=True)

        self.filter_funcs = [
            (self.do_lfilter, "lfilter"),
            (self.do_filtfilt, "filtfilt"),
            (self.do_sosfilt, "sosfilt"),
            (self.do_sosfiltfilt, "sosfiltfilt"),
        ]

    def check_attenuation(
        self, filtered_data, ref_val, truth, doPrint=False, checkFor=True
    ):
        """Helper function to check if the frequencies are attenuated.

        Args:
        ---
        filterd_data: 2D ndarray of filtered data. Assumed to be
            [n_samples, n_channel]
        ref_val: str, 'short' or 'long', to indicate which data set to
            check against
        truth: length n_freq list of booleans indicating whether
            each frequency should be attenuated.
        doPrint: boolean -- true to print out the Vout/Vin ratio.
        checkFor: boolean -- check that the given truth values match or not
        """

        # Use FFT to check frequency of the filtered data
        xf, xFFT = do_fft(filtered_data, dt=1.0 / self.fs, axis=0, dB=False)
        if ref_val == "short":
            mag_new = np.diag(xFFT[self.freq_idx_short, :])
            ratio = mag_new / self.mag_short
        elif ref_val == "long":
            mag_new = np.diag(xFFT[self.freq_idx_long, :])
            ratio = mag_new / self.mag_long
        if doPrint:
            print("Vout/Vin: ratio")

        answer = ratio <= np.sqrt(2) / 2  # -3dB attenuation as threshold
        self.assertEqual(np.all(answer == truth), checkFor)

    def test_butterworth_filter_shape_and_attenuation(self):
        """Test butter worth filter's shape and attenuation

        1) Filter the signals using different filters:
          lowpass, highpass, and bandpass
        2) Check output shape is correct
        3) Check the correct frequencies are attenuated

        To check frequency attenuation, check that the filtered signals'
        max value is at least 10% reduced compared from before. This attenuation
        is dependent on the cutoff frequency, and the test-frequencies are
        spaced far apart to detect this difference.

        This method only works when `linearPhase=False` because `filtfilt` will
        try to match the boundary conditions which we don't want.
        """

        print(f"Data shape = {self.data_short.shape}")
        # Now applying filter
        # 1) highpass (cutoff 7Hz, 4th order, lfilter)
        y_HPF = self.do_lfilter(
            self.data_short, cutoff=7, fs=self.fs, btype="high", order=4, axis=0
        )
        print(f"tf_filter: Data shape after highpass filter = {y_HPF.shape}")
        self.assertEqual(y_HPF.shape, self.data_short.shape)

        # high pass filtering at 7Hz, that means 5Hz are attenuated
        # are unaffected
        truth = [True, False, False]
        self.check_attenuation(y_HPF, "short", truth)

        y_HPF = self.do_sosfilt(
            self.data_short, cutoff=7, fs=self.fs, btype="high", order=4, axis=0
        )
        print(f"sos_filter: Data shape after highpass filter = {y_HPF.shape}")
        self.assertEqual(y_HPF.shape, self.data_short.shape)
        self.check_attenuation(y_HPF, "short", truth)

        # 2) bandpass (cutoff 7 - 40 Hz)
        y_BPF = self.do_lfilter(
            self.data_short,
            cutoff=[7, 40],
            fs=self.fs,
            btype="pass",
            order=4,
            axis=0,
            noDelay=False,
        )
        print(f"tf_filter: Data shape after bandpass filter = {y_BPF.shape}")
        self.assertEqual(y_BPF.shape, self.data_short.shape)

        # band pass filtering at 7-40 Hz, that means 5Hz and 45Hz are attenuated
        truth = [True, False, True]
        self.check_attenuation(y_BPF, "short", truth)

        y_BPF = self.do_sosfilt(
            self.data_short, cutoff=[7, 40], fs=self.fs, btype="pass", order=4, axis=0
        )
        print(f"sos_filter: Data shape after bandpass filter = {y_BPF.shape}")
        self.assertEqual(y_BPF.shape, self.data_short.shape)
        self.check_attenuation(y_BPF, "short", truth)

        # 3) LPF (cutoff 40Hz)
        y_LPF = self.do_lfilter(
            self.data_short, cutoff=40, fs=self.fs, btype="low", order=4, axis=0
        )
        print(f"tf_filter: Data shape after lowpass filter = {y_LPF.shape}")
        self.assertEqual(y_LPF.shape, self.data_short.shape)

        # low pass filtering at 40 Hz, that means 45Hz is attenuated
        truth = [False, False, True]
        self.check_attenuation(y_LPF, "short", truth)

        y_LPF = self.do_sosfilt(
            self.data_short, cutoff=40, fs=self.fs, btype="low", order=4, axis=0
        )
        print(f"sos_filter: Data shape after lowpass filter = {y_LPF.shape}")
        self.assertEqual(y_LPF.shape, self.data_short.shape)
        self.check_attenuation(y_LPF, "short", truth)

    def test_causal_butterworth(self):
        """Causal butterworth filter test"""
        # ===== 1) high pass =====
        cb = CausalButterworth(
            first_time_sample=self.data_long[0, :],
            cutoff=0.03,
            sample_freq=self.fs,
            btype="high",
        )
        results = []
        for i in range(self.data_long.shape[0]):
            results.append(cb.process_sample(sample=self.data_long[i, :]))
        y_HPF = np.vstack(results)

        # Check dimension
        self.assertEqual(np.all(self.data_long), np.all(y_HPF))

        # Check stability
        self.assertTrue(np.sum(np.isnan(y_HPF)) == 0)

        # high pass filtering at 0.03Hz, that means 0.01Hz are attenuated
        # are unaffected
        truth = [True, False, False]
        self.check_attenuation(y_HPF, "long", truth)

        # ===== 2) band pass =====
        cb = CausalButterworth(
            first_time_sample=self.data_long[0, :],
            cutoff=[0.02, 0.08],
            sample_freq=self.fs,
            btype="pass",
        )
        results = []
        for i in range(self.data_long.shape[0]):
            results.append(cb.process_sample(sample=self.data_long[i, :]))
        y_BPF = np.vstack(results)

        self.assertEqual(y_BPF.shape, self.data_long.shape)

        # Check stability
        self.assertTrue(np.sum(np.isnan(y_BPF)) == 0)

        # band pass filtering at 0.02-0.08 Hz, that means 0.01Hz and 0.1Hz are attenuated
        truth = [True, False, True]
        self.check_attenuation(y_BPF, "long", truth)

        # ===== 3) low pass =====
        cb = CausalButterworth(
            first_time_sample=self.data_long[0, :],
            cutoff=0.08,
            sample_freq=self.fs,
            btype="low",
        )
        results = []
        for i in range(self.data_long.shape[0]):
            results.append(cb.process_sample(sample=self.data_long[i, :]))
        y_LPF = np.vstack(results)

        self.assertEqual(y_LPF.shape, self.data_long.shape)

        # Check stability
        self.assertTrue(np.sum(np.isnan(y_LPF)) == 0)

        # low pass filtering at 0.08 Hz, that means 0.1Hz is attenuated
        truth = [False, False, True]
        self.check_attenuation(y_LPF, "long", truth)

    def test_butterworth_filter_axis(self):
        """Make sure when changing axis option, the results are different,
        if using the wrong option the results should not be right.
        """

        # Use the bandpass example, but filter channel-wise
        y_BPF = self.do_lfilter(
            self.data_short, cutoff=[7, 40], fs=self.fs, btype="pass", order=4, axis=1
        )
        print(f"Data shape after bandpass filter(axis=1) = {y_BPF.shape}")
        self.assertEqual(y_BPF.shape, self.data_short.shape)

        # band pass filtering at 7-40 Hz, that means 5Hz and 45Hz are attenuated
        truth = [True, False, True]
        # Make sure the result is not correct
        self.check_attenuation(y_BPF, "short", truth, checkFor=False)

        # Do it correctly!
        y_BPF = self.do_lfilter(
            self.data_short, cutoff=[7, 40], fs=self.fs, btype="pass", order=4, axis=0
        )
        print(f"Data shape after bandpass filter(axis=0) = {y_BPF.shape}")
        self.assertEqual(y_BPF.shape, self.data_short.shape)
        self.check_attenuation(y_BPF, "short", truth, checkFor=True)

    # Check stability
    def test_butterworth_filter_stability(self):
        """Test to make sure that sos filters are stable even for high
        filter order and narrow passband, while tf-filters are not.
        (If the second part of the test break, then that means scipy
         has changed..?)
        """

        # Test 1, data_short for testing
        # BPF[10, 30], 4th order
        # All filters should pass
        cutoff = np.array([10, 30])
        filter_order = 4
        for (func, func_name) in self.filter_funcs:
            print(f"Order {filter_order}, BPF({cutoff}), {func_name}")
            out = func(
                data=self.data_short,
                cutoff=cutoff,
                fs=self.fs,
                btype="pass",
                axis=0,
                order=filter_order,
            )
            self.check_attenuation(out, "short", [True, False, True])

        # Test 2, data_long for testing
        # BPF[0.02, 0.08], 4th order
        # Only the sos filters should pass
        filter_order = 4
        cutoff = np.array([0.02, 0.08])
        for (func, func_name) in self.filter_funcs[0:2]:
            print(f"Order {filter_order}, BPF({cutoff}), {func_name}")
            out = func(
                data=self.data_long,
                cutoff=cutoff,
                fs=self.fs,
                btype="pass",
                axis=0,
                order=filter_order,
            )
            self.check_attenuation(out, "long", [True, False, True], checkFor=False)

        for (func, func_name) in self.filter_funcs[2:]:
            print(f"Order {filter_order}, BPF({cutoff}), {func_name}")
            out = func(
                data=self.data_long,
                cutoff=cutoff,
                fs=self.fs,
                btype="pass",
                axis=0,
                order=filter_order,
            )
            self.check_attenuation(out, "long", [True, False, True], checkFor=True)

    # Check noDelay
    def test_butterworth_filter_noDelay(self):
        """Test to make sure that the noDelay option is working,
        really just means that we are using either `filtfilt` vs. `lfilter`,
        or `sosfilt` vs. `sosfiltfilt` here.

        Since the testing signals are cosine, y(0)=1

        Best way to check this is to see if the filtered signals' peaks
        line up in time with that of the original signal's.
        """

        filter_order = 4
        cutoff = np.array([10, 30])

        # Bandpass on data_short , check the peaks for the 25Hz signal
        # For lfilter and sos_filt
        for (func, func_name) in [self.filter_funcs[0], self.filter_funcs[2]]:
            print(f"Order {filter_order}, BPF({cutoff}), {func_name} peak-check")
            out = func(
                data=self.data_short,
                cutoff=cutoff,
                fs=self.fs,
                btype="pass",
                axis=0,
                order=filter_order,
            )
            peaks_new, _ = find_peaks(out[:, 1], height=0.5)
            # Should have the same number of peaks
            self.assertEqual(len(peaks_new), len(self.peaks_idx_short[1]))
            # The peaks should be spaced more than at least 1 samples apart
            self.assertTrue(np.all(np.abs(peaks_new - self.peaks_idx_short[1]) >= 1))

        # For filtfilt and sos_filtfilt
        for (func, func_name) in [self.filter_funcs[1], self.filter_funcs[3]]:
            print(f"Order {filter_order}, BPF({cutoff}), {func_name} peak-check")
            out = func(
                data=self.data_short,
                cutoff=cutoff,
                fs=self.fs,
                btype="pass",
                axis=0,
                order=filter_order,
            )
            peaks_new, _ = find_peaks(out[:, 1], height=0.5)
            # Should have the same number of peaks
            self.assertEqual(len(peaks_new), len(self.peaks_idx_short[1]))
            # The peaks should not be spaced more than at least 1 samples apart
            self.assertTrue(np.all(np.abs(peaks_new - self.peaks_idx_short[1]) < 1))

    def test_macd_filters(self):
        # Defining parameters to generate synthetic data
        duration = 200  # seconds
        sample_freq = 5  # Hz

        # ===== Create simulated data =====
        cardiac = dummy_physiological_noise(
            amplitude=0.3,
            sample_rate=sample_freq,
            interest_freq=1,
            phase=np.pi / 4,
            duration=duration,
        )
        slow_drift = dummy_physiological_noise(
            amplitude=0.1,
            sample_rate=sample_freq,
            interest_freq=0.01,
            phase=0,
            duration=duration,
        )
        interest_freq = 0.1
        important = dummy_physiological_noise(
            amplitude=0.3,
            sample_rate=sample_freq,
            interest_freq=interest_freq,
            phase=0,
            duration=duration,
        )
        signal = cardiac + slow_drift + important

        # ===== Do filtering (Causal) =====
        macd_results = [0]
        ema_on_macd = [0]
        for i in range(1, len(signal)):
            temp1 = moving_average_convergence_divergence(
                x=signal[i],
                y_prev=macd_results[i - 1],
                N_short=sample_freq * 5,
                N_long=sample_freq * 15,
            )
            macd_results.append(temp1)
            temp2 = exponential_moving_average(
                x=macd_results[i], y_prev=ema_on_macd[i - 1], N=10
            )
            ema_on_macd.append(temp2)
        ema_on_macd_np = np.array(ema_on_macd)

        # ===== Apply FFT =====
        xf_ema_macd, xFFT_ema_macd = do_fft(
            ema_on_macd_np, dt=1.0 / sample_freq, axis=0, dB=False
        )

        # ===== Get the peak, make sure it's the same frequency of interest =====
        peaks_ema_macd = find_peaks(xFFT_ema_macd, distance=duration * sample_freq / 2)
        self.assertAlmostEqual(*xf_ema_macd[peaks_ema_macd[0]], interest_freq)
