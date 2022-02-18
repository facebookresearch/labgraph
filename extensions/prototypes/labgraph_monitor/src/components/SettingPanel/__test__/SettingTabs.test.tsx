/**
 * Copyright (c) Facebook, Inc. and its affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */
import { render, screen } from '@testing-library/react';
import { store } from '../../../redux/store';
import { Provider } from 'react-redux';
import SettingTabs from '../SettingTabs';

const MockSettingTabs = () => {
    return (
        <Provider store={store}>
            <SettingTabs />
        </Provider>
    );
};

describe('SettingTabs', () => {
    it('should render SettingTabs component', async () => {
        render(<MockSettingTabs />);
        const settingPanel = screen.getByTestId('setting-tabs');
        expect(settingPanel).toBeInTheDocument();
    });
});
