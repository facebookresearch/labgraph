/**
 * Copyright (c) Facebook, Inc. and its affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */
import React from 'react';
import { RootState } from '../../redux/store';
import { useSelector } from 'react-redux';
import { Typography } from '@mui/material';
const Node: React.FC = (): JSX.Element => {
    const { selectedNode } = useSelector((state: RootState) => state.config);

    return (
        <React.Fragment>
            {selectedNode.id && <Typography>{selectedNode.id}</Typography>}
            {!selectedNode.id && (
                <Typography style={{ fontSize: '.8rem', fontWeight: 400 }}>
                    Click on a node to see its information
                </Typography>
            )}
        </React.Fragment>
    );
};

export default Node;
