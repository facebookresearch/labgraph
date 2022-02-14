import { useCallback, useState } from 'react';
import { TabContext, TabList, TabPanel } from '@mui/lab';
import {
    Box,
    Tab,
    MenuItem,
    InputLabel,
    FormControl,
    TextField,
    Button,
    Stack,
} from '@mui/material';
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

    textFieldLabel: {
        fontSize: '.85rem',
    },
});

const GraphSettings: React.FC = (): JSX.Element => {
    const classes = useStyles();
    const { mock, endPoint, setMock, setEndPoint } = useWSContext();
    const [value, setValue] = useState<string>('1');
    const [textField, setTextField] = useState<string>('');
    // const [isConnected, setIsConnected] = useState<boolean>(false);

    const handleChange = (_: React.SyntheticEvent, newValue: string) => {
        setValue(newValue);
    };

    const handleMockChange = (event: SelectChangeEvent) => {
        setMock(event.target.value);
    };

    const handleEndPointChange = (
        event: React.ChangeEvent<HTMLTextAreaElement | HTMLInputElement>
    ) => {
        setTextField(event?.target.value);
    };
    const handleConnect = useCallback(
        (event: React.FormEvent<HTMLFormElement>) => {
            event.preventDefault();
            if (!textField) return;
            setEndPoint(textField);
        },
        [textField, setEndPoint]
    );

    const handleDiconnect = (event: React.FormEvent<HTMLFormElement>) => {
        event.preventDefault();
        setEndPoint('');
        // setIsConnected(false);
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
                <TabPanel value="1">
                    <Box>
                        <form
                            onSubmit={
                                endPoint ? handleDiconnect : handleConnect
                            }
                        >
                            <FormControl sx={{ width: '100%' }}>
                                <TextField
                                    required
                                    id="outlined-basic"
                                    label="ENDPOINT"
                                    variant="outlined"
                                    placeholder="ws://127.0.0.1:9000"
                                    value={textField}
                                    size="small"
                                    inputProps={{
                                        pattern:
                                            'ws://127.0.0.1:[1-9][0-9]{3,4}',
                                    }}
                                    InputLabelProps={{
                                        style: { fontSize: '.8rem' },
                                    }}
                                    InputProps={{
                                        style: {
                                            padding: '2px',
                                            fontSize: '.85rem',
                                            letterSpacing: '1px',
                                        },
                                    }}
                                    onChange={handleEndPointChange}
                                />
                                <Stack
                                    style={{
                                        marginTop: 10,
                                    }}
                                >
                                    {endPoint ? (
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
                                id="mock-selectio"
                                value={mock}
                                label="Mock"
                                onChange={handleMockChange}
                            >
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
