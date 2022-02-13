import demo from '../demo.json';
import MOCK from '../enums/MOCK';

export const selectMock = (mock: string) => {
    switch (mock) {
        case MOCK.DEMO:
            return demo;

        default:
            return demo;
    }
};
