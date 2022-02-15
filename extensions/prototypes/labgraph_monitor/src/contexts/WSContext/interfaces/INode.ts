interface INode {
    [name: string]: {
        upstreams: {
            [upstream: string]: Array<{
                name: string;
                fields: {
                    [fieldName: string]: string;
                };
            }>;
        };
    };
}

export default INode;
