/**
 * Copyright (c) Facebook, Inc. and its affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */
import React from 'react';
import { RootState } from '../../redux/store';
import { useSelector } from 'react-redux';
const Node: React.FC = (): JSX.Element => {
    const { selectedNode } = useSelector((state: RootState) => state.config);

    return (
        <React.Fragment>
            <p style={{ padding: 10 }}>{selectedNode.id}</p>
        </React.Fragment>
    );
};

export default Node;
