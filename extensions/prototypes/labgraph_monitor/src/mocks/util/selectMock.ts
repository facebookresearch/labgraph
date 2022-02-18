/**
 * Copyright (c) Facebook, Inc. and its affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */
import demo from '../json/demo.json';
import simpleViz from '../json/simple_viz.json';
import simpleVizZMQ from '../json/simple_viz_zmq.json';
import simpleVizFixedRate from '../json/simple_viz_fixed_rate.json';
import simulation from '../json/simulation.json';
import MOCK from '../enums/MOCK';

/**
 * A function that picks a mock example based on the argument passed
 *
 * @param {string} mock the name of the mock example
 * @returns a parsed version of the JSON file containing the mock sample.
 */
export const selectMock = (mock: string) => {
    switch (mock) {
        case MOCK.SIMPLE_VIZ:
            return simpleViz;

        case MOCK.SIMULATION:
            return simulation;

        case MOCK.SIMPLE_VIZ_ZMQ:
            return simpleVizZMQ;

        case MOCK.SIMPLE_VIZ_FIXED_RATE:
            return simpleVizFixedRate;

        default:
            return demo;
    }
};
