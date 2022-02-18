/**
 * Copyright (c) Facebook, Inc. and its affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */
import { render, screen } from '@testing-library/react';
import { store } from '../../../redux/store';
import { Provider } from 'react-redux';
import NodeSettings from '../NodeSettings';

const MockNodeSettings = () => {
    return (
        <Provider store={store}>
            <NodeSettings />
        </Provider>
    );
};

describe('NodeSettings', () => {
    it('should render NodeSettings component', async () => {
        render(<MockNodeSettings />);
        const nodeSettings = screen.getByTestId('node-settings');
        expect(nodeSettings).toBeInTheDocument();
    });
});
