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
} from '@mui/icons-material';
import SettingTabs from './SettingTabs';
import { makeStyles } from '@mui/styles';
import { useUIContext } from '../../contexts';
import { RootState } from '../../redux/store';
import { useSelector, useDispatch } from 'react-redux';
import { setPanel } from '../../redux/reducers/config/configReducer';

const PANEL_WIDTH = 280;

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
        width: PANEL_WIDTH,
        flexShrink: 0,
        '& .MuiDrawer-paper': {
            width: PANEL_WIDTH,
        },
    },

    themeBar: {
        display: 'flex',
        width: '100%',
        justifyContent: 'space-around',
        alignItem: 'center',
        padding: '2px 4px 2px 4px',
    },
});

const SettingPanel: React.FC = (): JSX.Element => {
    const classes = useStyles();
    const { mode, layout, toggleMode, toggleLayout } = useUIContext();
    const { panelOpen } = useSelector((state: RootState) => state.config);
    const dispatch = useDispatch();

    return (
        <Box className={classes.root}>
            <CssBaseline />
            <IconButton
                onClick={() => dispatch(setPanel(true))}
                className={classes.settingButton}
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
                open={panelOpen}
            >
                <Box>
                    <IconButton onClick={() => dispatch(setPanel(false))}>
                        <ChevronRight />
                    </IconButton>
                </Box>
                <Divider />
                <Box className={classes.themeBar}>
                    <IconButton onClick={toggleMode}>
                        {mode === 'light' ? <DarkMode /> : <Brightness7 />}
                    </IconButton>
                    <IconButton onClick={toggleLayout}>
                        {layout === 'horizontal' ? (
                            <AlignVerticalTopOutlined />
                        ) : (
                            <AlignHorizontalLeftOutlined />
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
