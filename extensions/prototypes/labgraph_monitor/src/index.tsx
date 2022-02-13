import React from 'react';
import ReactDOM from 'react-dom';
import App from './App';
import { WSContextProvider, UIContextProvider } from './contexts';
import reportWebVitals from './reportWebVitals';
import './statics/css/global.css';

ReactDOM.render(
    <React.StrictMode>
        <UIContextProvider>
            <WSContextProvider>
                <App />
            </WSContextProvider>
        </UIContextProvider>
    </React.StrictMode>,
    document.getElementById('root')
);

reportWebVitals();
