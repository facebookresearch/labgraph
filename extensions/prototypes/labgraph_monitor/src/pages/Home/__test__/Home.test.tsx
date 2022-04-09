/**
 * Copyright (c) Facebook, Inc. and its affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */
import { render, screen } from '@testing-library/react';
import { store } from '../../../redux/store';
import { Provider } from 'react-redux';
import Home from '../Home';

const MockHome = () => {
    return (
        <Provider store={store}>
            <Home />
        </Provider>
    );
};

describe('Home', () => {
    it('should render Home component', async () => {
        render(<MockHome />);
        const settingPanel = screen.getByTestId('setting-panel');
        const graph = screen.getByTestId('graph');
        expect(settingPanel).toBeInTheDocument();
        expect(graph).toBeInTheDocument();
    });
});
