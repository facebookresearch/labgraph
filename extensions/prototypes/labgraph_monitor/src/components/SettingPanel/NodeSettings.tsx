/**
 * Copyright (c) Facebook, Inc. and its affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */
import React from 'react';
import { RootState } from '../../redux/store';
import { useSelector } from 'react-redux';
import { Box, Typography } from '@mui/material';

/**
 * A component that manages the settings of a node.
 * All components related to node settings should be children of this component.
 *
 * @returns {JSX.Element}
 */
const Node: React.FC = (): JSX.Element => {
    const { selectedNode } = useSelector((state: RootState) => state.config);

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
            </Box>
        </React.Fragment>
    );
};

export default Node;
