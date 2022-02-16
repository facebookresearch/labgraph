import React from 'react';
import ReactDOM from 'react-dom';
import App from './App';
import { WSContextProvider, UIContextProvider } from './contexts';
import reportWebVitals from './reportWebVitals';
import './statics/css/global.css';
import { store } from './redux/store';
import { Provider } from 'react-redux';

ReactDOM.render(
    <React.StrictMode>
        <UIContextProvider>
            <WSContextProvider>
                <Provider store={store}>
                    <App />
                </Provider>
            </WSContextProvider>
        </UIContextProvider>
    </React.StrictMode>,
    document.getElementById('root')
);

reportWebVitals();
