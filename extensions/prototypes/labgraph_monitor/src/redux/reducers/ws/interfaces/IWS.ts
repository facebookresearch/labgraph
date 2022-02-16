import IGraph from './IGraph';
import WS_STATE from '../enums/WS_STATE';

interface IWS {
    connection: WS_STATE;
    graph: IGraph;
}

export default IWS;
