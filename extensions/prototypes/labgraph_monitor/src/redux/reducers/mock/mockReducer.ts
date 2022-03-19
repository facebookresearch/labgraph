/**
 * Copyright (c) Facebook, Inc. and its affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */
import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import IGraph from './interfaces/IGraph';
import IMock from './interfaces/IMock';
import { selectMock } from '../../../mocks';

const initialState: IMock = {
    mockGraph: {} as IGraph,
    mockRealtimeData: [Date.now()],
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

        setMockRealtimeData: (state, action: PayloadAction<any>) => {
            state.mockRealtimeData = action.payload;
        },
    },
});

export const { copyRealtimeGraph, setMockGraph, setMockRealtimeData } =
    mockSlice.actions;

export default mockSlice.reducer;
