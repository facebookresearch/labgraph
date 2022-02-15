import React from 'react';
import { useConfigContext } from '../../contexts';
const Node: React.FC = (): JSX.Element => {
    const { selectedNode } = useConfigContext();

    return (
        <React.Fragment>
            <p style={{ padding: 10 }}>{selectedNode.id}</p>
        </React.Fragment>
    );
};

export default Node;
