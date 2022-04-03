/**
 * Copyright (c) Facebook, Inc. and its affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */
import { render, screen } from '@testing-library/react';
import { store } from '../../../redux/store';
import { Provider } from 'react-redux';
import GraphSettings from '../GraphSettings';

const MockGraphSettings = () => {
    return (
        <Provider store={store}>
            <GraphSettings />
        </Provider>
    );
};

describe('GraphSettings', () => {
    it('should render GraphSettings component', async () => {
        render(<MockGraphSettings />);
        const graphSettings = screen.getByTestId('graph-settings');
        expect(graphSettings).toBeInTheDocument();
    });
});
