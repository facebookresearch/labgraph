/**
 * Copyright (c) Facebook, Inc. and its affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */
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
