/**
 * Copyright (c) Facebook, Inc. and its affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */
enum WS_STATE {
    CONNECTED = 'CONNECTED',
    IS_CONNECTING = 'IS_CONNECTING',
    DISCONNECTED = 'DISCONNECTED',
    IS_DISCONNECTING = 'IS_DISCONNECTING',
}

export default WS_STATE;
