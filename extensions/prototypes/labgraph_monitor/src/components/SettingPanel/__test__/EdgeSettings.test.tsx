/**
 * Copyright (c) Facebook, Inc. and its affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */
import { render, screen } from '@testing-library/react';
import { store } from '../../../redux/store';
import { Provider } from 'react-redux';
import EdgeSettings from '../EdgeSettings';

const MockEdgeSettings = () => {
    return (
        <Provider store={store}>
            <EdgeSettings />
        </Provider>
    );
};

describe('EdgeSettings', () => {
    it('should render EdgeSettings component', async () => {
        render(<MockEdgeSettings />);
        const edgeSettings = screen.getByTestId('edge-settings');
        expect(edgeSettings).toBeInTheDocument();
    });
});
