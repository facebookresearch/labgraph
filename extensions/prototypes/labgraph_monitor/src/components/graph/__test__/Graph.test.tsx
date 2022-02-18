/**
 * Copyright (c) Facebook, Inc. and its affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */
import { render, screen } from '@testing-library/react';
import { store } from '../../../redux/store';
import { Provider } from 'react-redux';
import Graph from '../Graph';

const MockGraph = () => {
    return (
        <Provider store={store}>
            <Graph />;
        </Provider>
    );
};

describe('Graph', () => {
    it('should render Graph component', async () => {
        render(<MockGraph />);
        const graph = screen.getByTestId('graph');
        expect(graph).toBeInTheDocument();
    });
});
