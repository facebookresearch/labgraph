import React from 'react';
import ReactDOM from 'react-dom';
import App from './App';
import { GraphContextProvider } from './contexts';
import reportWebVitals from './reportWebVitals';
import './statics/css/global.css';

ReactDOM.render(
    <React.StrictMode>
        <GraphContextProvider>
            <App />
        </GraphContextProvider>
    </React.StrictMode>,
    document.getElementById('root')
);

reportWebVitals();
