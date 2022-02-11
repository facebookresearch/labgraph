import * as React from 'react';
import { Box, Drawer, CssBaseline, IconButton } from '@mui/material';
import MenuIcon from '@mui/icons-material/Menu';
import ChevronLeftIcon from '@mui/icons-material/ChevronLeft';

const PANEL_WIDTH = 350;

const SettingPanel: React.FC = (): JSX.Element => {
    const [open, setOpen] = React.useState(false);

    const handleDrawerOpen = () => {
        setOpen(true);
    };

    const handleDrawerClose = () => {
        setOpen(false);
    };

    return (
        <Box sx={{ display: 'flex' }}>
            <CssBaseline />
            <IconButton
                onClick={handleDrawerOpen}
                sx={{
                    position: 'absolute',
                    top: '10px',
                    right: '40px',
                    zIndex: '10',
                }}
            >
                <MenuIcon />
            </IconButton>
            <Drawer
                sx={{
                    width: PANEL_WIDTH,
                    flexShrink: 0,
                    '& .MuiDrawer-paper': {
                        width: PANEL_WIDTH,
                    },
                }}
                variant="persistent"
                anchor="right"
                open={open}
            >
                <Box>
                    <IconButton onClick={handleDrawerClose}>
                        <ChevronLeftIcon />
                    </IconButton>
                </Box>
            </Drawer>
        </Box>
    );
};

export default SettingPanel;
