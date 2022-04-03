/**
 * Copyright (c) Facebook, Inc. and its affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */
interface INode {
    id: string;
    data?: {
        label: string;
    };
    position: {
        x: number;
        y: number;
    };
    sourcePosition: 'left' | 'top' | 'right' | 'bottom';
    targetPosition: 'left' | 'top' | 'right' | 'bottom';
    style?: { [property: string]: string };
    className?: string;
}

export default INode;
