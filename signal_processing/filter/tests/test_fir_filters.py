#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

from __future__ import absolute_import, division, print_function, unicode_literals

import unittest

import mne
import numpy as np
from ..fir_filters import fir_filter


class FiniteImpulseResponseFilterTest(unittest.TestCase):
    def setUp(self):

        import scipy

        print(scipy.__version__)

        # ===== 1) Preparing data (for lowpass) =====
        # time length
        t_len = 50
        # sampling frequency
        sample_freq = 10
        x = np.linspace(0, t_len, t_len * sample_freq, endpoint=False)
        # making sure this has high power before filtering
        signal_4Hz = 2 * np.sin(2 * np.pi * 4 * x)
        signal_1Hz = np.sin(2 * np.pi * 1 * x)
        combined = signal_4Hz + signal_1Hz

        # before filtering
        power, freqs = mne.time_frequency.psd_array_multitaper(combined, sample_freq)
        power_log10 = np.log10(power)
        ind_of_peak = np.unravel_index(
            np.argmax(power_log10, axis=None), power_log10.shape
        )[0]
        # make sure 4 Hz has higher power
        self.assertEqual(freqs[ind_of_peak], 4.0)

        # Things needed for testing later
        self.data = combined  # data is [n_samples, ]
        self.filt_order = 50
        self.sample_freq = sample_freq

    def check_peak_freq(self, data, cutoff, fs, btype, order, axis, peak_freq):
        """Helper function to check that the filtered signal has the correct
        peak-frequncies.
        """
        filtered_data = fir_filter(
            data=data, cutoff=cutoff, fs=fs, btype=btype, order=order, axis=axis
        )

        # psd_aray_multitaper requires the inputs to be of dimension:
        # [..., n_times]
        # axis is suppoed to be n_times
        filtered_data_reshape = np.moveaxis(filtered_data, axis, -1)
        power, freqs = mne.time_frequency.psd_array_multitaper(
            filtered_data_reshape, fs
        )
        power_log10 = np.log10(power)
        ind_of_peak = np.argmax(power_log10, axis=-1)
        self.assertEqual(np.all(freqs[ind_of_peak] == peak_freq), True)

    def test_fir_filter_1D(self):
        """Test a simple FIR filter, input is one-dimensional

        1) Create dummy sine waves with different frequencies
           with one sine wave having higher amplitude = power
        2) Initial peak in PSD should show the frequency as dominant power
        3) Filter out using the filter
        4) This time the dominant power should be the other frequency
        """

        # ===== 2) Test lowpass =====
        # run filter lowpass
        cutoff = 2  # Hz -- peak should be 1Hz
        self.check_peak_freq(
            data=self.data,
            cutoff=cutoff,
            fs=self.sample_freq,
            btype=True,
            order=self.filt_order,
            axis=-1,
            peak_freq=np.array([1.0]),
        )

    def test_fir_filter_nD(self):
        """Test a simple lowpass FIR filter, input is multi-dimensional"""
        cutoff = 2  # Hz
        combined = np.vstack((self.data, self.data))  # dim is [2, n_samples]
        self.check_peak_freq(
            data=combined,
            cutoff=cutoff,
            fs=self.sample_freq,
            btype=True,
            order=self.filt_order,
            axis=1,
            peak_freq=np.array([1.0, 1.0]),
        )

    def test_fir_filter_axis(self):
        """Test lowpass FIR filter works even on nx1 or 1xn data

        Creating the correct initial condition shape can be tricky
        """
        cutoff = 2

        # Check column vector works
        col_data = self.data.reshape([-1, 1])
        print("test_fir_filter_axis: checking column vector input")
        self.check_peak_freq(
            data=col_data,
            cutoff=cutoff,
            fs=self.sample_freq,
            btype=True,
            order=self.filt_order,
            axis=0,
            peak_freq=np.array([1.0]),
        )

        # Check row vector works
        row_data = self.data.reshape([1, -1])
        print("test_fir_filter_axis: checking row vector input")
        self.check_peak_freq(
            data=row_data,
            cutoff=cutoff,
            fs=self.sample_freq,
            btype=True,
            order=self.filt_order,
            axis=1,
            peak_freq=np.array([1.0]),
        )

    def test_fir_filter_linearPhase(self):
        """Test lowpass FIR filter produces linear phase delay

        1) Generate sample waveform
        2) Lowpass with different filter order
        3) Check that the different filtered signals are delayed by roughly
           order/2 samples. This is done by looking through multiple periods
           and find where the peaks are, and compare the sample number.

        Use different signals here to chose nice numbers to check
        """

        fs = 50
        duration = 1.0
        t = np.arange(0, duration, 1.0 / fs)
        sin_10Hz = np.sin(2 * np.pi * 10 * t).reshape([-1, 1])  # col vector
        cutoff = 20  # 20Hz lowpass, signal shouldn't be affected much

        # signal's peaks
        nPeaks = 8
        signal_peaks = []
        for cur_order in [2, 4, 6, 8]:
            y_LPF = fir_filter(
                sin_10Hz, cutoff=cutoff, fs=fs, btype=True, order=cur_order, axis=0
            )
            y_LPF_peaks = []
            for i in range(nPeaks):
                # find peaks -- period every 5 samples
                idx_start = i * 5
                idx_end = (i + 1) * 5
                y_LPF_peaks.append(np.argmax(y_LPF[idx_start:idx_end]))
                if len(signal_peaks) < nPeaks:
                    signal_peaks.append(np.argmax(sin_10Hz[idx_start:idx_end]))

            mean_delay = np.mean(np.array(y_LPF_peaks) - np.array(signal_peaks))
            # if mean_delay is negative, that means the first peak of the
            # filtered signal is now closer to the second peak of the original
            if mean_delay < 0:
                print("mean_delay=" + str(mean_delay) + " adjust by period")
                mean_delay = 5 + mean_delay
            self.assertEqual(np.rint(mean_delay), cur_order / 2)
