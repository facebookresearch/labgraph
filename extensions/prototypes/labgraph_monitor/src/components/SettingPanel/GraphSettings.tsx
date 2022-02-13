import { useState } from 'react';
import { TabContext, TabList, TabPanel } from '@mui/lab';
import { Box, Tab, MenuItem, InputLabel, FormControl } from '@mui/material';
import { makeStyles } from '@mui/styles';
import Select, { SelectChangeEvent } from '@mui/material/Select';
import { MOCK } from '../../mocks';
import { useWSContext } from '../../contexts';

const useStyles = makeStyles({
    root: {
        width: '100%',
    },

    tab: {
        width: '50%',
    },
    tabLabel: {
        fontSize: '.85rem',
        fontWeight: 400,
    },

    selectInputLabel: {
        fontSize: '0.8rem',
    },
});

const GraphSettings: React.FC = (): JSX.Element => {
    const classes = useStyles();
    const { mock, setMock } = useWSContext();
    const [value, setValue] = useState<string>('1');

    const handleChange = (event: React.SyntheticEvent, newValue: string) => {
        setValue(newValue);
    };

    const handleMockChange = (event: SelectChangeEvent) => {
        console.log(event.target.value);
        setMock(event.target.value);
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
                        <Tab
                            className={classes.tab}
                            label={
                                <span className={classes.tabLabel}>
                                    realtime
                                </span>
                            }
                            value="1"
                        />
                        <Tab
                            className={classes.tab}
                            label={
                                <span className={classes.tabLabel}>mock</span>
                            }
                            value="2"
                        />
                    </TabList>
                </Box>
                <TabPanel value="1">realtime</TabPanel>
                <TabPanel value="2">
                    <Box>
                        <FormControl sx={{ width: '100%' }}>
                            <InputLabel
                                style={{ fontSize: '.8rem' }}
                                id="mock-selection-bar"
                            >
                                Mock
                            </InputLabel>
                            <Select
                                style={{ fontSize: '.8rem' }}
                                labelId="mock-selection-bar"
                                id="mock-selectio"
                                value={mock}
                                onChange={handleMockChange}
                                label="Mock"
                            >
                                {Object.entries(MOCK).map(
                                    ([key, value], index) => {
                                        return (
                                            <MenuItem
                                                key={key}
                                                style={{ fontSize: '.8rem' }}
                                                value={value}
                                            >
                                                {value}
                                            </MenuItem>
                                        );
                                    }
                                )}
                            </Select>
                        </FormControl>
                    </Box>
                </TabPanel>
            </TabContext>
        </Box>
    );
};

export default GraphSettings;
