#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

from __future__ import absolute_import, division, print_function, unicode_literals

import unittest

import numpy as np
import scipy
from ..fir_filters import symmetric_fir_group_delay
from ..iir_filters import butter_group_delay, butter_sos, CausalButterworth
from ..signal_transforms import (
    do_fft,
    filter_freq_response,
    filter_group_delay,
    filter_impulse_response,
    filter_phase_delay,
)


class SignalTransformsTest(unittest.TestCase):
    def setUp(self):
        self.dt = 1 / 100
        self.t = np.arange(0, 10, self.dt)  # 100Hz

        # FFT magnitude for the different freq
        self.mag_10Hz = 5
        self.mag_15Hz = 2.5
        self.mag_DC = 1
        # [n_samples, ]
        self.x_1D = (
            2 * self.mag_10Hz * np.cos(2 * np.pi * 10 * self.t)
            + 2 * self.mag_15Hz * np.cos(2 * np.pi * 15 * self.t)
            + self.mag_DC
        )

        # [n_samples, 2]
        self.x_2D = np.hstack((self.x_1D.reshape([-1, 1]), self.x_1D.reshape([-1, 1])))

        # [2, n_samples, 2]
        self.x_3D = np.concatenate(
            (np.expand_dims(self.x_2D, axis=0), np.expand_dims(self.x_2D, axis=0)),
            axis=0,
        )
        # second 'page' has no DC
        self.x_3D[1, :, :] = self.x_3D[1, :, :] - 1

    # Basic 1D fft
    def test_FFT_1D(self):
        xf, xFFT = do_fft(self.x_1D, self.dt)

        # Check 10Hz freq component
        self.assertAlmostEqual(xFFT[np.argwhere(xf == 10)][0][0], self.mag_10Hz, 3)
        self.assertAlmostEqual(xFFT[np.argwhere(xf == -10)][0][0], self.mag_10Hz, 3)

        # Check 15Hz freq component
        self.assertAlmostEqual(xFFT[np.argwhere(xf == 15)][0][0], self.mag_15Hz, 3)
        self.assertAlmostEqual(xFFT[np.argwhere(xf == -15)][0][0], self.mag_15Hz, 3)

        # Check DC freq component
        self.assertAlmostEqual(xFFT[np.argwhere(xf == 0)][0][0], self.mag_DC, 3)

        # Use dB values
        xf, xFFT_dB = do_fft(self.x_1D, self.dt, dB=True)
        # Check 10Hz freq component
        val = 20 * np.log10(self.mag_10Hz)
        self.assertAlmostEqual(xFFT_dB[np.argwhere(xf == 10)][0][0], val, 3)
        self.assertAlmostEqual(xFFT_dB[np.argwhere(xf == -10)][0][0], val, 3)

        # Check 15Hz freq component
        val = 20 * np.log10(self.mag_15Hz)
        self.assertAlmostEqual(xFFT_dB[np.argwhere(xf == 15)][0][0], val, 3)
        self.assertAlmostEqual(xFFT_dB[np.argwhere(xf == -15)][0][0], val, 3)

        # Check DC freq component
        val = 20 * np.log10(self.mag_DC)
        self.assertAlmostEqual(xFFT_dB[np.argwhere(xf == 0)][0][0], val, 3)

    # 2D FFT
    def test_FFT_2D(self):
        xf, xFFT = do_fft(self.x_2D, self.dt, axis=0)

        # Check 10Hz freq component
        self.assertEqual(
            np.all(xFFT[np.argwhere(xf == 10)[0][0], :] - self.mag_10Hz < 1e-3), True
        )
        self.assertEqual(
            np.all(xFFT[np.argwhere(xf == -10)[0][0], :] - self.mag_10Hz < 1e-3), True
        )

        # Check 15Hz freq component
        self.assertEqual(
            np.all(xFFT[np.argwhere(xf == 15)[0][0], :] - self.mag_15Hz < 1e-3), True
        )
        self.assertEqual(
            np.all(xFFT[np.argwhere(xf == -15)[0][0], :] - self.mag_15Hz < 1e-3), True
        )

        # Check DC freq component
        self.assertEqual(
            np.all(xFFT[np.argwhere(xf == 0)[0][0], :] - self.mag_DC < 1e-3), True
        )

    # 3D FFT
    def test_FFT_3D(self):
        xf, xFFT = do_fft(self.x_3D, self.dt, axis=1)

        # Check 10Hz freq component
        for page in range(1):
            for f in [10, -10]:
                idx = np.argwhere(xf == f)[0][0]
                self.assertEqual(
                    np.all(xFFT[page, idx, :] - self.mag_10Hz < 1e-3), True
                )

        # Check 15Hz freq component
        for page in range(1):
            for f in [15, -15]:
                idx = np.argwhere(xf == f)[0][0]
                self.assertEqual(
                    np.all(xFFT[page, idx, :] - self.mag_15Hz < 1e-3), True
                )

        # Check DC freq component
        self.assertEqual(
            np.all(xFFT[0, np.argwhere(xf == 0)[0][0], :] - self.mag_DC < 1e-3), True
        )
        # Second page has no DC component
        self.assertEqual(
            np.all(xFFT[1, np.argwhere(xf == 0)[0][0], :] - 0 < 1e-3), True
        )

    def test_filter_impulse_response(self):
        """
        Get impulse response of 2048 points, for 5th-order IIR filter
        with bandwidth [0.01, 0.1]Hz, sampling frequency of 10Hz
        """
        N = 2048
        fs = 10.0
        bandwidth = (0.01, 0.1)

        order = 5
        sos_iir = butter_sos(bandwidth, fs=fs, btype="bandpass", order=order)
        iir_impulse_response, time = filter_impulse_response(sos_iir, N, fs, sos=True)

        self.assertTrue(
            np.abs(iir_impulse_response[0]) < 1e-6
        )  # impulse response starts at 0
        np.testing.assert_array_almost_equal(
            iir_impulse_response,
            scipy.signal.sosfilt(sos_iir, scipy.signal.unit_impulse(N)),
        )
        np.testing.assert_array_almost_equal(time, np.arange(0, 2048 / fs, 1 / fs))

        """
        Get impulse response of 2048 points, for a 25-tap FIR filter with
        bandwidth [0.01, 0.1]Hz, sampling frequency of 10Hz
        """
        n_coefs = 25
        fir_coefs = scipy.signal.firwin(n_coefs, bandwidth, pass_zero=False, fs=fs)
        fir_impulse_response, time = filter_impulse_response(
            fir_coefs, N, fs, sos=False
        )
        self.assertTrue(
            fir_impulse_response[-1] == 0
        )  # FIR impulse response is finite!
        np.testing.assert_array_almost_equal(
            fir_impulse_response,
            scipy.signal.lfilter(b=fir_coefs, a=1, x=scipy.signal.unit_impulse(N)),
        )

    def test_filter_freq_response(self):
        """
        Get frequency response of a 5th-order IIR filter
        with bandwidth [0.01, 0.1]Hz, sampling frequency of 10Hz
        """
        N = 2048
        fs = 10.0
        bandwidth = (0.01, 0.1)
        order = 5
        sos_iir = butter_sos(bandwidth, fs=fs, btype="bandpass", order=order)

        # check freq response is roughly flat between 0.01 and 0.06Hz
        freq, magnitude, phase = filter_freq_response(sos_iir, N, fs)
        np.testing.assert_array_almost_equal(
            magnitude[(freq >= 0.01) & (freq <= 0.06)], 1, decimal=2
        )
        # check phase response at 0 starts at -pi
        # sosfreqz has phase response starting at 0
        self.assertTrue(np.abs(phase[0] - -np.pi) < 1e-3)

    def test_filter_phase_delay_iir(self):
        """
        Check phase delay at near center band for 5th order
        butterworth bandpass filter, with bandwidth (0.01, 0.1)Hz,
        sampling frequency of 10Hz.

        The phase delay at 0.05Hz should be about 33 samples.
        """
        N = 2048
        fs = 10.0
        bandwidth = (0.01, 0.1)
        test_freq = 0.05
        order = 5
        sos_iir = butter_sos(bandwidth, fs=fs, btype="bandpass", order=order)
        freq, phase_delay = filter_phase_delay(sos_iir, N, fs)
        self.assertTrue(
            np.abs(phase_delay[np.argmin(np.abs(freq - test_freq))] - 33) < 1
        )

    def test_filter_group_delay_fir(self):
        """
        Group delay calculated via impulse response and
        symmetric_fir_group_delay should match for
        over 98% of the frequencies (mismatch due to numerical
        errors)
        """
        n_coefs = 25
        bandwidth = (0.01, 0.1)
        fs = 10
        fir_coefs = scipy.signal.firwin(n_coefs, bandwidth, pass_zero=False, fs=fs)
        symmetric_gd = symmetric_fir_group_delay(fir_coefs)
        _, impulse_gd = filter_group_delay(fir_coefs, fs=fs, sos=False)
        self.assertTrue(
            np.sum(np.abs(impulse_gd - symmetric_gd) < 1) / len(impulse_gd) >= 0.98
        )
