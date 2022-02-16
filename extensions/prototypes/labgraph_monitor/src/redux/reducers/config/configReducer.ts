import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { Edge, Node } from 'react-flow-renderer';
import IConfig from './interfaces/IConfig';

const initialState: IConfig = {
    panelOpen: false,
    tabIndex: '1',
    selectedNode: {} as Node,
    selectedEdge: {} as Edge,
};

export const configSlice = createSlice({
    name: 'config',
    initialState,
    reducers: {
        setPanel: (state, action: PayloadAction<boolean>) => {
            state.panelOpen = action.payload;
        },
        setTabIndex: (state, action: PayloadAction<string>) => {
            state.tabIndex = action.payload;
        },

        setSelectedNode: (state, action: PayloadAction<Node>) => {
            state.selectedNode = action.payload;
        },

        setSelectedEdge: (state, action: PayloadAction<Edge>) => {
            state.selectedEdge = action.payload;
        },
    },
});

export const { setPanel, setTabIndex, setSelectedNode, setSelectedEdge } =
    configSlice.actions;

export default configSlice.reducer;
