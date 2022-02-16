import React from 'react';
import { Graph, SettingPanel } from '../../components';
import { WSContextProvider } from '../../contexts';

const Home: React.FC = (): JSX.Element => {
    return (
        <React.Fragment>
            <SettingPanel />
            <WSContextProvider>
                <Graph />
            </WSContextProvider>
        </React.Fragment>
    );
};

export default Home;
