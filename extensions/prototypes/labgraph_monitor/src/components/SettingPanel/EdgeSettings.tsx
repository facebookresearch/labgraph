import {
    Paper,
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow,
} from '@mui/material';
import React from 'react';
import { useConfigContext, useWSContext } from '../../contexts';

const Edge: React.FC = (): JSX.Element => {
    const { selectedEdge } = useConfigContext();

    const { graph } = useWSContext();

    const messages =
        graph && selectedEdge.target
            ? graph['nodes'][selectedEdge.target]['upstreams'][
                  selectedEdge.source
              ]
            : [];
    return (
        <React.Fragment>
            {messages.map((message, index) => {
                return (
                    <TableContainer key={index} component={Paper}>
                        <Table sx={{ width: '100%' }} aria-label="simple table">
                            <TableHead>
                                <TableRow>
                                    <TableCell>{message['name']}</TableCell>
                                </TableRow>
                            </TableHead>
                            <TableBody>
                                {Object.entries(message['fields']).map(
                                    ([name, type]) => {
                                        return (
                                            <TableRow key={name}>
                                                <TableCell>{name}</TableCell>
                                                <TableCell>{type}</TableCell>
                                            </TableRow>
                                        );
                                    }
                                )}
                            </TableBody>
                        </Table>
                    </TableContainer>
                );
            })}
        </React.Fragment>
    );
};

export default Edge;
