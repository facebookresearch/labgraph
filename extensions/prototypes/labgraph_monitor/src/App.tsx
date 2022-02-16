/**
 * Copyright (c) Facebook, Inc. and its affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */
import { Home } from './pages';

const App: React.FC = (): JSX.Element => {
    return (
        <div className="App" style={{ height: '100vh' }}>
            <Home />
        </div>
    );
};

export default App;
