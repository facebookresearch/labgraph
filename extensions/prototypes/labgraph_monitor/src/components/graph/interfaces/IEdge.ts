interface IEdge {
    id: string;
    label?: string;
    source: string;
    target: string;
    arrowHeadType?: 'arrow' | 'arrowclosed';
    type?: 'default' | 'straight' | 'step' | 'smoothstep';
    animated?: boolean;
}

export default IEdge;
