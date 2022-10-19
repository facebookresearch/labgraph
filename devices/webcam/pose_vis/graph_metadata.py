import labgraph as lg

from pose_vis.video_stream import GraphMetaData

class GraphMetaDataProviderConfig(lg.Config):
    num_streams: int

class GraphMetaDataProvider(lg.Node):
    OUTPUT = lg.Topic(GraphMetaData)
    config: GraphMetaDataProviderConfig

    @lg.publisher(OUTPUT)
    async def send_metadata(self) -> lg.AsyncPublisher:
        yield self.OUTPUT, GraphMetaData(num_streams = self.config.num_streams)