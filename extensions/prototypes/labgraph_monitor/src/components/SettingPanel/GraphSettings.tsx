/**
 * Copyright (c) Facebook, Inc. and its affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */
import { useState } from 'react';
import { TabContext, TabList, TabPanel } from '@mui/lab';
import {
    Box,
    Tab,
    MenuItem,
    InputLabel,
    FormControl,
    Button,
    Stack,
} from '@mui/material';
import { makeStyles } from '@mui/styles';
import Select, { SelectChangeEvent } from '@mui/material/Select';
import { MOCK } from '../../mocks';
import { useDispatch, useSelector } from 'react-redux';
import { RootState } from '../../redux/store';
import { setMockGraph } from '../../redux/reducers/mock/mockReducer';
import { setConnection } from '../../redux/reducers/ws/WSReducer';
import WS_STATE from '../../redux/reducers/ws/enums/WS_STATE';

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

    textFieldLabel: {
        fontSize: '.85rem',
    },
});

const GraphSettings: React.FC = (): JSX.Element => {
    const classes = useStyles();
    const { connection } = useSelector((state: RootState) => state.ws);
    const [value, setValue] = useState<string>('1');
    const [mock, setMock] = useState<string>('');
    const dispatch = useDispatch();

    const handleChange = (_: React.SyntheticEvent, newValue: string) => {
        setValue(newValue);
    };

    const handleMockChange = (event: SelectChangeEvent) => {
        dispatch(setMockGraph(event.target.value));
        setMock(event.target.value);
    };

    const handleConnect = (event: React.FormEvent<HTMLFormElement>) => {
        event.preventDefault();
        dispatch(setConnection(WS_STATE.IS_CONNECTING));
    };

    const handleDiconnect = (event: React.FormEvent<HTMLFormElement>) => {
        event.preventDefault();
        dispatch(setConnection(WS_STATE.IS_DISCONNECTING));
    };

    return (
        <Box className={classes.root} data-testid="graph-settings">
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
                <TabPanel value="1">
                    <Box>
                        <form
                            onSubmit={
                                connection === WS_STATE.CONNECTED
                                    ? handleDiconnect
                                    : handleConnect
                            }
                        >
                            <FormControl sx={{ width: '100%' }}>
                                <Stack
                                    style={{
                                        marginTop: 10,
                                    }}
                                >
                                    {connection === WS_STATE.CONNECTED ? (
                                        <Button
                                            type="submit"
                                            variant="outlined"
                                        >
                                            disconnect
                                        </Button>
                                    ) : (
                                        <Button
                                            type="submit"
                                            variant="outlined"
                                        >
                                            connect
                                        </Button>
                                    )}
                                </Stack>
                            </FormControl>
                        </form>
                    </Box>
                </TabPanel>
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
                                id="mock-selection"
                                label="Mock"
                                value={mock}
                                onChange={handleMockChange}
                            >
                                <MenuItem value="">
                                    <em>Mock</em>
                                </MenuItem>
                                {Object.entries(MOCK).map(([key, value]) => {
                                    return (
                                        <MenuItem
                                            key={key}
                                            style={{ fontSize: '.8rem' }}
                                            value={value}
                                        >
                                            {value}
                                        </MenuItem>
                                    );
                                })}
                            </Select>
                        </FormControl>
                    </Box>
                </TabPanel>
            </TabContext>
        </Box>
    );
};

export default GraphSettings;
