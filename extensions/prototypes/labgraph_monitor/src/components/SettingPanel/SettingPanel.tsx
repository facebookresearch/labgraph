/**
 * Copyright (c) Facebook, Inc. and its affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */
import { Box, Drawer, CssBaseline, IconButton, Divider } from '@mui/material';
import {
    ChevronRight,
    Brightness7,
    DarkMode,
    SettingsApplicationsRounded,
    AlignHorizontalLeftOutlined,
    AlignVerticalTopOutlined,
    Mode,
} from '@mui/icons-material';
import React, { useCallback } from 'react';
import SettingTabs from './SettingTabs';
import { makeStyles } from '@mui/styles';
import { useUIContext } from '../../contexts';
import { RootState } from '../../redux/store';
import { useSelector, useDispatch } from 'react-redux';
import { setPanel } from '../../redux/reducers/config/configReducer';

export const DEFAULT_PANEL_WIDTH = 280;
export const MIN_PANEL_WIDTH = 280;
export const MAX_PANEL_WIDTH = 600;
const useStyles = makeStyles({
    root: {
        display: 'flex',
    },

    settingButton: {
        position: 'absolute',
        top: '10px',
        right: '20px',
        zIndex: '10',
    },

    settingIcon: {
        '&:hover': {
            opacity: 0.9,
        },
    },

    settingPanel: {
        width: DEFAULT_PANEL_WIDTH,
        flexShrink: 0,
        '& .MuiDrawer-paper': {
            width: DEFAULT_PANEL_WIDTH,
        },
    },

    themeBar: {
        display: 'flex',
        width: '100%',
        justifyContent: 'space-around',
        alignItem: 'center',
        padding: '2px 4px 2px 4px',
    },
    dragger_light: {
        width: '5px',
        cursor: 'ew-resize',
        padding: '4px 0 0',
        borderTop: '1px solid #ddd',
        position: 'absolute',
        top: 0,
        left: 0,
        bottom: 0,
        zIndex: '100',
        backgroundColor: '#f4f7f9',
    },
    dragger_dark: {
        width: '5px',
        cursor: 'ew-resize',
        padding: '4px 0 0',
        borderTop: '1px solid #111827',
        position: 'absolute',
        top: 0,
        left: 0,
        bottom: 0,
        zIndex: '100',
        backgroundColor: '#1f2b3c',
    },
});

/**
 * A component that represents the setting panel of the application.
 * All components related to UI or Graph settings should be children of this component.
 *
 * @returns {JSX.Element}
 */
const SettingPanel: React.FC = (): JSX.Element => {
    const classes = useStyles();
    const { mode, layout, toggleMode, toggleLayout } = useUIContext();
    const { panelOpen } = useSelector((state: RootState) => state.config);
    const dispatch = useDispatch();
    const [panelWidth, setPanelWidth] = React.useState(DEFAULT_PANEL_WIDTH);
    const handleMouseDown = () => {
        document.addEventListener('mouseup', handleMouseUp, true);
        document.addEventListener('mousemove', handleMouseMove, true);
    };
    const handleMouseUp = () => {
        document.removeEventListener('mouseup', handleMouseUp, true);
        document.removeEventListener('mousemove', handleMouseMove, true);
    };
    const handleMouseMove = useCallback((e) => {
        const newWidth =
            document.body.offsetLeft + document.body.offsetWidth - e.clientX;
        if (newWidth > MIN_PANEL_WIDTH && newWidth < MAX_PANEL_WIDTH) {
            setPanelWidth(newWidth);
        }
    }, []);
    return (
        <Box className={classes.root} data-testid="setting-panel">
            <CssBaseline />
            <IconButton
                onClick={() => dispatch(setPanel(true))}
                className={classes.settingButton}
                data-testid="open-setting-btn"
                sx={{
                    display: panelOpen ? 'none' : 'block',
                    position: 'absolute',
                    '&:hover, &.Mui-focusVisible': {
                        backgroundColor: 'transparent',
                    },
                }}
            >
                <SettingsApplicationsRounded
                    className={classes.settingIcon}
                    sx={{
                        width: 40,
                        height: 40,
                    }}
                />
            </IconButton>
            <Drawer
                className={classes.settingPanel}
                variant="persistent"
                anchor="right"
                PaperProps={{ style: { width: panelWidth } }}
                open={panelOpen}
            >
                <Box>
                    <IconButton
                        onClick={() => dispatch(setPanel(false))}
                        data-testid="close-setting-btn"
                    >
                        <ChevronRight />
                    </IconButton>
                </Box>

                <div
                    id="dragger"
                    onMouseDown={() => handleMouseDown()}
                    className={
                        mode === 'light'
                            ? classes.dragger_light
                            : classes.dragger_dark
                    }
                />

                <Divider />
                <Box className={classes.themeBar}>
                    <IconButton
                        onClick={toggleMode}
                        data-testid="toggle-mode-btn"
                    >
                        {mode === 'light' ? (
                            <DarkMode data-testid="dark-mode-icon" />
                        ) : (
                            <Brightness7 data-testid="light-mode-icon" />
                        )}
                    </IconButton>
                    <IconButton
                        onClick={toggleLayout}
                        data-testid="toggle-layout-btn"
                    >
                        {layout === 'horizontal' ? (
                            <AlignVerticalTopOutlined data-testid="vertical-layout-icon" />
                        ) : (
                            <AlignHorizontalLeftOutlined data-testid="horizontal-layout-icon" />
                        )}
                    </IconButton>
                </Box>
                <Divider />
                <SettingTabs />
            </Drawer>
        </Box>
    );
};

export default SettingPanel;
