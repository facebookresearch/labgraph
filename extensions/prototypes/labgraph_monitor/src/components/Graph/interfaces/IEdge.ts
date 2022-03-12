/**
 * Copyright (c) Facebook, Inc. and its affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */
interface IEdge {
    id: string;
    label?: string;
    source: string;
    target: string;
    arrowHeadType?: 'arrow' | 'arrowclosed';
    type?: 'default' | 'straight' | 'step' | 'smoothstep';
    animated?: boolean;
    style?: { [property: string]: string };
    className?: string;
}

export default IEdge;
