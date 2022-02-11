import React from 'react';
import { Graph, SettingPanel } from '../../components';

const Home: React.FC = (): JSX.Element => {
    return (
        <React.Fragment>
            <SettingPanel />
            <Graph />
        </React.Fragment>
    );
};

export default Home;
