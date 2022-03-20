#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

import unittest

import numpy as np
from ..additive_synth_dataset_variant import (
    AdditiveSynthDatasetVariant,
    generate_synth_data,
    hrf_scale_from_channel_dists,
)


sample_rate = 10
trial_length = 26
hrf_scale = 1


class AdditiveSyntheticDatasetVariantTest(unittest.TestCase):
    @unittest.skip("only for manual local testing")
    def test_generate_synth_data_one_trial(self):

        trial = generate_synth_data(hrf_scale, sample_rate, trial_length)
        self.assertEqual(len(trial), trial_length * sample_rate)

    def test_generate_synth_data_multiple_channels(self):
        class_labels = ["0", "1", "2"]
        n_channels = 9
        hrf_scale_for_cond = np.zeros((n_channels, len(np.unique(class_labels))))
        hrf_scale_for_cond[0:2, 0] = 0.8  # first 10 channels responsive to cond1
        hrf_scale_for_cond[3:5, 1] = 0.7  # second 10 channels responsive to cond2
        hrf_scale_for_cond[6:8, 2] = 0  # second 10 channels responsive to cond3
        n_trials = 10
        trial_length = 26
        channel_dists = [10, 10, 10, 20, 20, 20, 30, 30, 30]
        sample_rate = 10
        data = AdditiveSynthDatasetVariant(
            n_trials,
            trial_length,
            channel_dists,
            class_labels,
            hrf_scale_for_cond,
            sample_rate,
        )

        X = np.zeros(
            (data.n_trials, data.n_channels, int(trial_length * sample_rate))
        )  # output data

        hrf_scales_from_distance = hrf_scale_from_channel_dists(channel_dists)

        for trial in range(n_trials):
            for label in range(len(class_labels)):
                for channel, hrf_scale_from_distance in enumerate(
                    hrf_scales_from_distance
                ):
                    hrf_scale_final = (
                        hrf_scale_from_distance * hrf_scale_for_cond[channel, label]
                    )
                    X[trial, channel, :] = generate_synth_data(
                        hrf_scale_final, data.sample_rate, data.trial_length
                    )

        # check dimensions for returned data, should be similar to output data (X)
        self.assertEqual(X.shape, (10, 9, 260))
