/**
 * Copyright (c) Facebook, Inc. and its affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */
interface IUIContext {
    mode: 'light' | 'dark';
    toggleMode: () => void;
    layout: 'horizontal' | 'vertical';
    toggleLayout: () => void;
}

export default IUIContext;
