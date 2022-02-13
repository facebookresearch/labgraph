interface INode {
    [name: string]: {
        inputs: Array<{
            name: string;
            type: string;
        }>;
        upstreams: Array<string>;
    };
}

export default INode;
