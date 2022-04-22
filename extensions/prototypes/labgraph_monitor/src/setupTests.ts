/**
 * Copyright (c) Facebook, Inc. and its affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */
import '@testing-library/jest-dom';
import '@testing-library/jest-dom/extend-expect';
import ResizeObserver from 'resize-observer-polyfill';

global.ResizeObserver = ResizeObserver;
global.alert = (content: string) => {
    console.log('Window alert mock - ', content);
};
