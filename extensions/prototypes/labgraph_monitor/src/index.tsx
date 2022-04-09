/**
 * Copyright (c) Facebook, Inc. and its affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */
import React from 'react';
import ReactDOM from 'react-dom';
import App from './App';
import { UIContextProvider } from './contexts';
import reportWebVitals from './reportWebVitals';
import './statics/css/global.css';
import { store } from './redux/store';
import { Provider } from 'react-redux';

ReactDOM.render(
    <React.StrictMode>
        <UIContextProvider>
            <Provider store={store}>
                <App />
            </Provider>
        </UIContextProvider>
    </React.StrictMode>,
    document.getElementById('root')
);

reportWebVitals();
