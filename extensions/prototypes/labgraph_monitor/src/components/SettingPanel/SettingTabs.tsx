/**
 * Copyright (c) Facebook, Inc. and its affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */
import { TabContext, TabList, TabPanel } from '@mui/lab';
import { Box, Tab } from '@mui/material';
import { makeStyles } from '@mui/styles';
import NodeSettings from './NodeSettings';
import EdgeSettings from './EdgeSettings';
import GraphSettings from './GraphSettings';
import { RootState } from '../../redux/store';
import { useSelector, useDispatch } from 'react-redux';
import { setTabIndex } from '../../redux/reducers/config/configReducer';

const useStyles = makeStyles({
    root: {
        width: '100%',
    },
    tab: {
        width: '33%',
    },
});

/**
 * A component that categorizes settings within the settings panel
 *
 * @returns {JSX.Element}
 */
const SettingTabs: React.FC = (): JSX.Element => {
    const classes = useStyles();
    const { tabIndex } = useSelector((state: RootState) => state.config);
    const dispatch = useDispatch();
    return (
        <Box className={classes.root} data-testid="setting-tabs">
            <TabContext value={tabIndex}>
                <Box
                    sx={{
                        borderBottom: 1,
                        borderColor: 'divider',
                    }}
                >
                    <TabList
                        onChange={(event, newValue) =>
                            dispatch(setTabIndex(newValue))
                        }
                        data-testid="tab-list"
                    >
                        <Tab label="graph" value="1" className={classes.tab} />
                        <Tab label="node" value="2" className={classes.tab} />
                        <Tab label="edge" value="3" className={classes.tab} />
                    </TabList>
                </Box>
                <TabPanel style={{ padding: 0 }} value="1">
                    <GraphSettings />
                </TabPanel>
                <TabPanel style={{ padding: 8 }} value="2">
                    <NodeSettings />
                </TabPanel>
                <TabPanel style={{ padding: 8 }} value="3">
                    <EdgeSettings />
                </TabPanel>
            </TabContext>
        </Box>
    );
};

export default SettingTabs;
