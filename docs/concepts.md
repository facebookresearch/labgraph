# LabGraph Concepts

The fundamental units of systems built with LabGraph are:

* [**Messages**](#messages)
* [**Streams**](#streams-and-topics)
* [**Topics**](#streams-and-topics)
* [**Nodes**](#nodes)
* [**Groups**](#groups)
* [**Graphs**](#graphs)

Together, these concepts allow us to construct [real-time](https://en.wikipedia.org/wiki/Real-time_computing) computational [graphs](https://en.wikipedia.org/wiki/Graph_(discrete_mathematics). These are "networks" of algorithms working together to produce some result within a time constraint. We want to be able to iterate on systems we build this way as efficiently as possible, which is what LabGraph is designed to enable. By enabling the fast plug-and-play of different nodes in such a graph, we can rapidly try out different hardware sensors, preprocessing pipelines, machine learning models, and user interfaces.

In this overview we will use a toy example of a simple visualization. The example is intended to illustrate the end-to-end combination of a data source, processing step, and user interface. While this may not seem like a useful piece of software to build, this example is a jumping-off point that is extensible to any combination of hardware, processing, and UI.

## Messages

A **message** is a piece of data with a consistent structure. For example:

```
import numpy as np
import labgraph.v1 as lg

class RandomMessage(lg.Message):
    timestamp: float
    data: np.ndarray
```
Here, we define two fields:

* `timestamp`, a float which associates a timestamp with the data.
* `data`, a numpy array that stores some data (which we will generate randomly in this example)

This should look familiar if you are familiar with [dataclasses](https://docs.python.org/3/library/dataclasses.html) or [named tuples](https://docs.python.org/3/library/collections.html#collections.namedtuple) in Python – these are libraries that allow the concise construction of simple data-wrapping classes using Python typehints. Like these builtin libraries, LabGraph relies on Python type hints to allow users to specify how data is composed. As you'll see when we look at groups, LabGraph relies heavily on type hints in general for composition.

To create a message, we simply create an instance of the `RandomMessage` class:

```
import time
random_message = RandomMessage(
    timestamp=time.time(), data=np.random.rand(100)
)
# Now LabGraph can use random_message
```
Suppose we were running an experiment where someone presses a button, and we wanted to include the state of the button with every frame. We could just add a `button_pressed` field to `RandomMessage`, but this would couple `RandomMessage` with that experiment and make reusing it with other experiments harder. Instead, we can **compose message types** via class inheritance (in the same way that the `dataclasses` module allows):

```
class CustomMessage(RandomMessage):
  button_pressed: bool
```
Then `CustomMessage` retains all the fields of `RandomMessage`, and we can instantiate it like so:

```
custom_message = CustomMessage(
  timestamp=time.time(),
  data=np.random.rand(100),
  button_pressed=True,
)
```
## Streams and Topics

A **stream** is a sequence of messages that is accessible in real-time. Streams are a useful construct when we want to build systems that respond in real-time to input from a hardware device. In this example we will stream `RandomMessage` which is not particularly useful, but you could imagine a sensor stream instead in an experimental setting.

A **topic** is a named reference to a stream. This is useful because we usually want to refer to a stream by different names in different contexts.

We'll see how to create topics when we discuss nodes below, and we'll see how to create streams when we discuss groups.

## Nodes

A **node** is a class that describes a self-contained algorithm that operates on topics. Nodes have the following properties:

* They define topics which act as inputs and outputs for streams
* They describe their algorithms using methods that are marked with special LabGraph "decorators"
* They are guaranteed to always be running in the same Python process throughout the life of a graph, with access to the same memory. This means a node can store state that is unique to the algorithm it implements.

Nodes describe their algorithms using methods that are marked with special LabGraph decorators. Here is an example of a node that takes a rolling average of some data:

```
class RollingState(lg.State):
    messages: List[RandomMessage] = field(default_factory=list)

class RollingConfig(lg.Config):
    window: float

class RollingAverager(lg.Node):
    INPUT = lg.Topic(RandomMessage)
    OUTPUT = lg.Topic(RandomMessage)

    state: RollingState
    config: RollingConfig

    @lg.subscriber(INPUT)
    @lg.publisher(OUTPUT)
    async def average(self, message: RandomMessage) -> lg.AsyncPublisher:
        current_time = time.time()
        self.state.messages.append(message)
        self.state.messages = [
            message
            for message in self.state.messages
            if message.timestamp >= current_time - self.config.window
        ]
        if len(self.state.messages) == 0:
            return
        all_data = np.stack([message.data for message in self.state.messages])
        mean_data = np.mean(all_data, axis=0)
        yield self.OUTPUT, RandomMessage(timestamp=current_time, data=mean_data)
```
First, we define some state & configuration - see [Lifecycles and Configuration](lifecycles-and-configuration.md) for details. Then we define the `RollingAverager` node:

* We define two topics, `INPUT` and `OUTPUT` which are references to streams of type `RandomMessage`. These topics are local to the `RolingAverager` node; it is the only node that can interact with them. When we construct a graph, we can point these topics at whatever streams we want.
* We define a method `average` to describe the averaging algorithm.
   * The **subscriber** decorator indicates that this method subscribes to the `INPUT` topic. Whenever a message is sent into the stream that the `INPUT` topic points to, the `average` method will be called with that message.
   * The **publisher** decorator indicates that this method publishes to the `OUTPUT` topic.
   * The `async` keyword indicates that this is a asyncio-enabled method. [asyncio](https://docs.python.org/3/library/asyncio.html) is a builtin Python library for writing concurrent code.
   * `AsyncPublisher` is a typehint provided by LabGraph to help type publisher functions..
   * The averaging algorithm produces an average sample by looking at all previous samples over the window.
   * The `yield` keyword is used to publish messages using asyncio. We yield a tuple containing the topic and the message to be published.

## Groups

A **group** is a container that includes some functionality that can be reused much like a node can be. A group can contain nodes, as well as other groups. As a result, groups enable composition and swappability of subgraphs.

Suppose we wanted a way to quickly package together a data source and a transformation of that data. Here is a `Generator` node, as well as a group that packages it with `RollingAverager` above:

```
class GeneratorConfig(lg.Config):
    sample_rate: float
    num_features: int

class Generator(lg.Node):
    OUTPUT = lg.Topic(RandomMessage)
    config: GeneratorConfig

    @lg.publisher(OUTPUT)
    async def generate_noise(self) -> lg.AsyncPublisher:
        while True:
            yield self.OUTPUT, RandomMessage(
                timestamp=time.time(), data=np.random.rand(self.config.num_features)
            )
            await asyncio.sleep(1 / self.config.sample_rate)

class AveragedNoiseConfig(lg.Config):
    sample_rate: float
    num_features: int
    window: float

class AveragedNoise(lg.Group):
    OUTPUT = lg.Topic(RandomMessage)

    config: AveragedNoiseConfig
    GENERATOR: Generator
    ROLLING_AVERAGER: RollingAverager

    def connections(self) -> lg.Connections:
        return (
            (self.GENERATOR.OUTPUT, self.ROLLING_AVERAGER.INPUT),
            (self.ROLLING_AVERAGER.OUTPUT, self.OUTPUT),
        )

    def setup(self) -> None:
        # Cascade configuration to contained nodes
        self.GENERATOR.configure(
            GeneratorConfig(
                sample_rate=self.config.sample_rate,
                num_features=self.config.num_features,
            )
        )
        self.ROLLING_AVERAGER.configure(RollingConfig(window=self.config.window))
```
* We create an output topic for the group - other groups that contain this group can connect to this topic
* We assign a configuration to this group that contains all the information both nodes require
* We add the type annotations `GENERATOR` and `ROLLING_AVERAGER` to indicate that each `AveragedNoise` group contains these nodes.
* The `connections` method lets us specify how topics will be connected. When two topics are connected, it means they will point to the same stream at runtime. In this case we specify that the `OUTPUT` topic of the `Generator` will be connected to the `INPUT` topic of the `RollingAverager`. We also create the `OUTPUT` topic in `AveragedNoise` that basically exposes the output stream from `RollingAverager`.

Now we can use `AveragedNoise` as if it were a node – it is a self-contained module that we can reuse anywhere we want.

## Graphs

A **graph** is a complete set of topics and nodes that describes a functioning system. It is actually a group, but it is assumed to be the outermost container for the description of a system. Suppose we want to display a live visualization using our group from earlier. We can define a graph as follows:

```
class Demo(lg.Graph):
    AVERAGED_NOISE: AveragedNoise
    PLOT: Plot

    def setup(self) -> None:
        self.AVERAGED_NOISE.configure(
            AveragedNoiseConfig(
                sample_rate=SAMPLE_RATE, num_features=NUM_FEATURES, window=WINDOW
            )
        )
        self.PLOT.configure(
            PlotConfig(refresh_rate=REFRESH_RATE, num_bars=NUM_FEATURES)
        )

    def connections(self) -> lg.Connections:
        return ((self.AVERAGED_NOISE.OUTPUT, self.PLOT.INPUT),)

    def process_modules(self) -> Tuple[lg.Module, ...]:
        return (self.AVERAGED_NOISE, self.PLOT)
```
* We add the `AVERAGED_NOISE` group from before, as well as a `Plot` node (implementation left out) that displays a live bar graph in a UI.
* Since graphs are groups, we can use `connections()` to connect `AveragedNoise` to `Plot`.
* Graphs have the additional functionality of being able to define `process_modules()` which lets us specify the process architecture of the groups and nodes the graph contains. In this case, by returning `(self.AVERAGED_NOISE, self.PLOT)` from this method, we cause the `AveragedNoise` group and the `Plot` node to run in separate processes. If we excluded this method, everything would run in a single process. In this way, `process_modules()` lets us concisely specify how a graph should be parallelized.

Then we can run the graph using the `lg.run()` tool:

```
if __name__ == "__main__":
  lg.run(Demo)
```
That's it! This will run the graph, which will generate noise and display it in real-time.
