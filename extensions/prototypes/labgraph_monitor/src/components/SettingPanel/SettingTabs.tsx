import { useState } from 'react';
import { TabContext, TabList, TabPanel } from '@mui/lab';
import { Box, Tab } from '@mui/material';
import { makeStyles } from '@mui/styles';

const useStyles = makeStyles({
    root: {
        width: '100%',
    },
});

const SettingTabs: React.FC = (): JSX.Element => {
    const classes = useStyles();
    const [value, setValue] = useState<string>('1');

    const handleChange = (event: React.SyntheticEvent, newValue: string) => {
        setValue(newValue);
    };

    return (
        <Box className={classes.root}>
            <TabContext value={value}>
                <Box
                    sx={{
                        borderBottom: 1,
                        borderColor: 'divider',
                    }}
                >
                    <TabList onChange={handleChange}>
                        <Tab label="graph" value="1" />
                        <Tab label="node" value="2" />
                        <Tab label="edge" value="3" />
                    </TabList>
                </Box>
                <TabPanel value="1">Graph</TabPanel>
                <TabPanel value="2">Node</TabPanel>
                <TabPanel value="3">Edge</TabPanel>
            </TabContext>
        </Box>
    );
};

export default SettingTabs;
