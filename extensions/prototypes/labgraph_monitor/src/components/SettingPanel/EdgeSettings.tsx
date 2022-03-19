/**
 * Copyright (c) Facebook, Inc. and its affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */
import {
    Box,
    Paper,
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow,
    Typography,
    Card,
    Switch,
    Button,
    Backdrop,
} from '@mui/material';
import React, { useEffect } from 'react';
import { RootState } from '../../redux/store';
import { useDispatch, useSelector } from 'react-redux';
import WS_STATE from '../../redux/reducers/ws/enums/WS_STATE';
import { setMockRealtimeData } from '../../redux/reducers/mock/mockReducer';

/**
 * A component that manages the settings of an edge.
 * All components related to edge settings should be children of this component.
 *
 * @returns {JSX.Element}
 */
const Edge: React.FC = (): JSX.Element => {
    const { selectedEdge } = useSelector((state: RootState) => state.config);
    const { connection, graph: realtimeGraph } = useSelector(
        (state: RootState) => state.ws
    );
    const { mockGraph, mockRealtimeData } = useSelector(
        (state: RootState) => state.mock
    );

    const mockData = useSelector((s: RootState) => s.mock.mockRealtimeData);

    const graph = connection === WS_STATE.CONNECTED ? realtimeGraph : mockGraph;

    const messages =
        graph && selectedEdge.target
            ? graph['nodes'][selectedEdge.target]['upstreams'][
                  selectedEdge.source
              ]
            : [];
    const [open, setOpen] = React.useState(false);
    const handleClose = () => {
        setOpen(false);
    };
    const handleToggle = () => {
        setOpen(!open);
    };

    // creating mock data, check mockReducer.ts, IMock.ts and EdgeSettings.tsx for future updates
    const dispatch = useDispatch();

    useEffect(() => {
        const id = setInterval(() => {
            const date = Date.now();

            dispatch(
                setMockRealtimeData([date, date % 10, date * 3, date / 4])
            );
        }, 1000);

        return () => {
            clearInterval(id);
        };
    }, []);

    return (
        <React.Fragment>
            <Box data-testid="edge-settings">
                {messages.map((message, index) => {
                    return (
                        <TableContainer key={index} component={Paper}>
                            <Table
                                sx={{ width: '100%' }}
                                aria-label="edge table contains the name, type of the edge"
                            >
                                <TableHead>
                                    <TableRow>
                                        <TableCell>{message['name']}</TableCell>
                                    </TableRow>
                                </TableHead>
                                <TableBody>
                                    {/* ZMQMessage Edge */}
                                    {Object.entries(message['fields']).map(
                                        ([name, type]) => {
                                            return (
                                                <TableRow key={name}>
                                                    <TableCell>
                                                        {name}
                                                    </TableCell>
                                                    <TableCell>
                                                        {type}
                                                    </TableCell>
                                                </TableRow>
                                            );
                                        }
                                    )}

                                    <TableRow>
                                        <Button onClick={handleToggle}>
                                            Show Realtime Data
                                        </Button>
                                        <Backdrop
                                            sx={{
                                                color: '#fff',
                                                zIndex: (theme) =>
                                                    theme.zIndex.drawer + 1,
                                            }}
                                            open={open}
                                            onClick={handleClose}
                                        >
                                            {/* Dummy data */}
                                            <Card
                                                style={{
                                                    width: 500,
                                                    padding: 20,
                                                }}
                                            >
                                                [{mockData.join(', ')}]
                                            </Card>
                                        </Backdrop>
                                    </TableRow>
                                </TableBody>
                            </Table>
                        </TableContainer>
                    );
                })}

                {!messages.length && (
                    <Typography style={{ fontSize: '.8rem', fontWeight: 400 }}>
                        Click on an edge to see the message information
                    </Typography>
                )}
            </Box>
        </React.Fragment>
    );
};

export default Edge;
