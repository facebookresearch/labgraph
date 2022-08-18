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
    // TableHead,
    TableRow,
    Typography,
    Button,
} from '@mui/material';
import React, { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import WS_STATE from '../../redux/reducers/graph/ws/enums/WS_STATE';
import { setMockRealtimeData } from '../../redux/reducers/graph/mock/mockReducer';
import { RootState } from '../../redux/store';

interface IMessage {
    name: string;
    fields: {
        [fieldName: string]: {
            type: string;
            content: any;
        };
    };
}
/**
 * A component that manages the settings of a node.
 * All components related to node settings should be children of this component.
 *
 * @returns {JSX.Element}
 */
const Node: React.FC = (): JSX.Element => {
    const { selectedNode } = useSelector((state: RootState) => state.config);

    const { selectedEdge } = useSelector((state: RootState) => state.config);
    const { connection, graph: realtimeGraph } = useSelector(
        (state: RootState) => state.ws
    );
    const { mockGraph } = useSelector((state: RootState) => state.mock);
    // const mockData = useSelector(
    //     (state: RootState) => state.mock.mockRealtimeData
    // );
    const graph = connection === WS_STATE.CONNECTED ? realtimeGraph : mockGraph;
    const [open, setOpen] = React.useState(false);

    const messages: IMessage[] =
        graph && selectedEdge.target
            ? graph['nodes'][selectedEdge.target]['upstreams'][
                  selectedEdge.source
              ]
            : [];
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
        }, 100);

        return () => clearInterval(id);
    }, [dispatch]);

    return (
        <React.Fragment>
            <Box data-testid="node-settings">
                {selectedNode?.id ? (
                    <Typography>{selectedNode.id}</Typography>
                ) : (
                    <Typography style={{ fontSize: '.8rem', fontWeight: 400 }}>
                        Click on a node to see its information
                    </Typography>
                )}
                {messages.map((message: IMessage, index) => {
                    return (
                        <TableContainer key={index} component={Paper}>
                            <Table
                                sx={{ width: '100%' }}
                                aria-label="simple table"
                            >
                                <TableBody>
                                    {/* ZMQMessage Edge */}
                                    <br></br>
                                    <Button onClick={handleToggle}>
                                        {open ? 'Show less' : 'Show more'}
                                    </Button>

                                    {Object.entries(message.fields).map(
                                        (field, index) => {
                                            return (
                                                <TableRow key={index}>
                                                    {open ? (
                                                        <TableCell
                                                            style={{
                                                                whiteSpace:
                                                                    'normal',
                                                                wordBreak:
                                                                    'break-word',
                                                            }}
                                                        >
                                                            {connection ===
                                                                WS_STATE.CONNECTED &&
                                                            (field[0] ===
                                                                'latency' ||
                                                                field[0] ===
                                                                    'throughput' ||
                                                                field[0] ===
                                                                    'datarate')
                                                                ? `${field[0]} `
                                                                : null}
                                                        </TableCell>
                                                    ) : null}
                                                    {open ? (
                                                        <TableCell
                                                            style={{
                                                                whiteSpace:
                                                                    'normal',
                                                                wordBreak:
                                                                    'break-word',
                                                            }}
                                                        >
                                                            {connection ===
                                                                WS_STATE.CONNECTED &&
                                                            (field[0] ===
                                                                'latency' ||
                                                                field[0] ===
                                                                    'throughput' ||
                                                                field[0] ===
                                                                    'datarate')
                                                                ? `${field[1].content} `
                                                                : null}
                                                        </TableCell>
                                                    ) : null}
                                                </TableRow>
                                            );
                                        }
                                    )}
                                </TableBody>
                            </Table>
                        </TableContainer>
                    );
                })}
            </Box>
        </React.Fragment>
    );
};

export default Node;
