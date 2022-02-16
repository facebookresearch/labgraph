import { configureStore } from '@reduxjs/toolkit';
import configReducer from './reducers/config/configReducer';
import mockReducer from './reducers/mock/mockReducer';
import WSReducer from './reducers/ws/WSReducer';

export const store = configureStore({
    reducer: {
        config: configReducer,
        mock: mockReducer,
        ws: WSReducer,
    },
    middleware: (getDefaultMiddleware) =>
        getDefaultMiddleware({
            serializableCheck: false,
        }),
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
