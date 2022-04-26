/**
 * Copyright (c) Facebook, Inc. and its affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */
interface INode {
    [name: string]: {
        upstreams: {
            [upstream: string]: Array<{
                name: string;
                fields: {
                    [fieldName: string]: {
                        type: string;
                        content: number | number[];
                    };
                };
            }>;
        };
    };
}

export default INode;
