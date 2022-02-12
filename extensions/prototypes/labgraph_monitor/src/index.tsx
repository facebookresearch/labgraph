import React from 'react';
import ReactDOM from 'react-dom';
import App from './App';
import { GraphContextProvider, UIContextProvider } from './contexts';
import reportWebVitals from './reportWebVitals';
import './statics/css/global.css';

ReactDOM.render(
    <React.StrictMode>
        <UIContextProvider>
            <GraphContextProvider>
                <App />
            </GraphContextProvider>
        </UIContextProvider>
    </React.StrictMode>,
    document.getElementById('root')
);

reportWebVitals();
