import demo from '../json/demo.json';
import simpleViz from '../json/simple_viz.json';
import simpleVizZMQ from '../json/simple_viz_zmq.json';
import simpleVizFixedRate from '../json/simple_viz_fixed_rate.json';
import simulation from '../json/simulation.json';
import MOCK from '../enums/MOCK';

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
