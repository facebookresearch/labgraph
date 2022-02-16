/**
 * Copyright (c) Facebook, Inc. and its affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */
import { Dispatch, SetStateAction } from 'react';
import IGraph from './IGraph';

interface IWSContext {
    graph: IGraph;
    mock: string;
    setMock: Dispatch<SetStateAction<string>>;
    endPoint: string;
    setEndPoint: Dispatch<SetStateAction<string>>;
    isConnected: boolean;
    setIsConnected: Dispatch<SetStateAction<boolean>>;
}

export default IWSContext;
