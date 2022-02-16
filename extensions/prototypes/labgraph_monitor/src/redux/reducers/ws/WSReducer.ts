import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import IWS from './interfaces/IWS';
import IGraph from './interfaces/IGraph';
import WS_STATE from './enums/WS_STATE';

const initialState: IWS = {
    connection: WS_STATE.DISCONNECTED,
    graph: {} as IGraph,
};

const WSSlice = createSlice({
    name: 'ws',
    initialState,
    reducers: {
        setConnection: (state, action: PayloadAction<WS_STATE>) => {
            state.connection = action.payload;
        },

        setGraph: (state, action: PayloadAction<IGraph>) => {
            state.graph = action.payload;
        },
    },
});

export const { setConnection, setGraph } = WSSlice.actions;

export default WSSlice.reducer;
