import React from 'react';
import { useConfigContext, useWSContext } from '../../contexts';

const Edge: React.FC = (): JSX.Element => {
    const { selectedEdge } = useConfigContext();

    const { graph } = useWSContext();

    const messages =
        graph['nodes'][selectedEdge.target]['upstreams'][selectedEdge.source];
    return (
        <React.Fragment>
            {messages.map((message, index) => {
                return (
                    <div
                        key={index}
                        style={{
                            background: '#fff',
                            padding: '2px 4px 2px 4px',
                            color: 'inhrent',
                        }}
                    >
                        <h6>{message['name']}</h6>
                        {Object.entries(message['fields']).map(
                            ([name, type]) => {
                                return (
                                    <div key={name}>
                                        {name}:{type}
                                    </div>
                                );
                            }
                        )}
                    </div>
                );
            })}
        </React.Fragment>
    );
};

export default Edge;
