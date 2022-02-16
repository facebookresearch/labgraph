import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import IGraph from './interfaces/IGraph';
import IMock from './interfaces/IMock';
import { selectMock } from '../../../mocks';

const initialState: IMock = {
    mockGraph: {} as IGraph,
};

export const mockSlice = createSlice({
    name: 'mock',
    initialState,
    reducers: {
        setMockGraph: (state, action: PayloadAction<string>) => {
            const {
                stream_batch: {
                    'labgraph.monitor': { samples },
                },
            } = selectMock(action.payload);

            state.mockGraph = samples[0]['data'];
        },

        copyRealtimeGraph: (state, action: PayloadAction<IGraph>) => {
            state.mockGraph = action.payload;
        },
    },
});

export const { copyRealtimeGraph, setMockGraph } = mockSlice.actions;

export default mockSlice.reducer;
