import React from 'react';
import ReactDOM from 'react-dom';
import App from './App';
import {
    WSContextProvider,
    UIContextProvider,
    ConfigContextProvider,
} from './contexts';
import reportWebVitals from './reportWebVitals';
import './statics/css/global.css';

ReactDOM.render(
    <React.StrictMode>
        <UIContextProvider>
            <WSContextProvider>
                <ConfigContextProvider>
                    <App />
                </ConfigContextProvider>
            </WSContextProvider>
        </UIContextProvider>
    </React.StrictMode>,
    document.getElementById('root')
);

reportWebVitals();
