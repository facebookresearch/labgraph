interface INode {
    [name: string]: {
        upstreams: {
            [upstream: string]: Array<{
                name: string;
                type: string;
            }>;
        };
    };
}

export default INode;
