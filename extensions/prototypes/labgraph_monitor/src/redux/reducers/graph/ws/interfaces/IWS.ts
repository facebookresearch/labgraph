/**
 * Copyright (c) Facebook, Inc. and its affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */
import IGraph from '../../common/interfaces/IGraph';
import WS_STATE from '../enums/WS_STATE';

interface IWS {
    connection: WS_STATE;
    graph: IGraph;
}

export default IWS;
