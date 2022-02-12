import { useState } from 'react';
import { Box, Drawer, CssBaseline, IconButton, Divider } from '@mui/material';
import SettingsApplicationsRoundedIcon from '@mui/icons-material/SettingsApplicationsRounded';
import ChevronRightIcon from '@mui/icons-material/ChevronRight';
import Brightness7Icon from '@mui/icons-material/Brightness7';
import DarkModeIcon from '@mui/icons-material/DarkMode';
import AlignHorizontalLeftOutlinedIcon from '@mui/icons-material/AlignHorizontalLeftOutlined';
import AlignVerticalTopOutlinedIcon from '@mui/icons-material/AlignVerticalTopOutlined';
import SettingTabs from './SettingTabs';
import { makeStyles } from '@mui/styles';
import { useUIContext } from '../../contexts';

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
    const { mode, layout, toggleMode, toggleLayout } = useUIContext();
    const [open, setOpen] = useState<boolean>(false);
    const classes = useStyles();

    const handleDrawerOpen = () => {
        setOpen(true);
    };

    const handleDrawerClose = () => {
        setOpen(false);
    };

    return (
        <Box className={classes.root}>
            <CssBaseline />
            <IconButton
                onClick={handleDrawerOpen}
                className={classes.settingButton}
                sx={{
                    display: open ? 'none' : 'block',
                    position: 'absolute',
                    '&:hover, &.Mui-focusVisible': {
                        backgroundColor: 'transparent',
                    },
                }}
            >
                <SettingsApplicationsRoundedIcon
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
                open={open}
            >
                <Box>
                    <IconButton onClick={handleDrawerClose}>
                        <ChevronRightIcon />
                    </IconButton>
                </Box>
                <Divider />
                <Box className={classes.themeBar}>
                    <IconButton onClick={toggleMode}>
                        {mode === 'light' ? (
                            <DarkModeIcon />
                        ) : (
                            <Brightness7Icon />
                        )}
                    </IconButton>
                    <IconButton onClick={toggleLayout}>
                        {layout === 'horizontal' ? (
                            <AlignVerticalTopOutlinedIcon />
                        ) : (
                            <AlignHorizontalLeftOutlinedIcon />
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
