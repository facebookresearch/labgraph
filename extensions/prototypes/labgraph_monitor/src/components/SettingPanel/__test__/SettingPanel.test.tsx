/**
 * Copyright (c) Facebook, Inc. and its affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */
import { render, screen, fireEvent } from '@testing-library/react';
import { store } from '../../../redux/store';
import { Provider } from 'react-redux';
import SettingPanel from '../SettingPanel';

const MockSettingPanel = () => {
    return (
        <Provider store={store}>
            <SettingPanel />
        </Provider>
    );
};

describe('SettingPanel', () => {
    it('should render SettingPanel component', async () => {
        render(<MockSettingPanel />);
        const settingPanel = screen.getByTestId('setting-panel');
        expect(settingPanel).toBeInTheDocument();
    });

    it('should toggle mode', async () => {
        render(<MockSettingPanel />);
        const toggleModeBtn = screen.getByTestId('toggle-mode-btn');
        fireEvent.click(toggleModeBtn);
        const lightModeIcon = screen.getByTestId('light-mode-icon');
        const darkModeIcon = screen.queryByText('dark-mode-icon');
        expect(lightModeIcon).toBeInTheDocument();
        expect(darkModeIcon).toBeNull();
    });

    it('should toggle layout', async () => {
        render(<MockSettingPanel />);
        const toggleLayoutBtn = screen.getByTestId('toggle-layout-btn');
        fireEvent.click(toggleLayoutBtn);
        const horizontalLayoutIcon = screen.getByTestId(
            'horizontal-layout-icon'
        );
        const verticalLayoutIcon = screen.queryByText('vertical-layout-icon');
        expect(horizontalLayoutIcon).toBeInTheDocument();
        expect(verticalLayoutIcon).toBeNull();
    });
});
