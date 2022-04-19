# Module Lifecycle

A node, group, or graph (a module) goes through the following steps in its lifetime:

1. **Definition**: The module type is defined in Python code which the Python interpreter reads into memory.
2. **Construction**: We construct an instance of the module. If the module is a graph, then the user explicitly constructs a graph like `graph = MyGraph()`. Otherwise, a module is implicitly constructed by its containing graph when that graph is constructed.
3. **Setup**: As a LabGraph graph is starting up, `setup()` is called on every module. If a group contains some other modules, the group's `setup()` will always be called before those modules' `setup()`s are called. During the `setup()` call, the module can prepare itself for execution. If the module is a group, then it can also configure the modules it contains - see [Configuration](#configuration).
4. **Execution**: When the graph is ready, LabGraph will begin execution of all modules simultaneously.
5. **Cleanup**: When all modules have terminated, LabGraph will run `cleanup()` on every module. `cleanup()` will be called in the same order that `setup()` was called.

# Configuration

LabGraph provides a way to concisely specify configuration that is given to a graph and forwarded to its descendant nodes. We start by defining a configuration type:

```python
class MyNodeConfig(df.Config):
  num_trials: int
  participant_name: str
```
`Config` classes actually just `Message` classes, except that they also provide special utilities for configuring graphs, as you'll see.



We specify the configuration for a `Node`, `Group`, or `Graph` by giving it a `config` type annotation:

```python
class MyNode(df.Node):
  config: MyNodeConfig

  ...
```
Then we can configure it by calling `configure()` on it. We configure a node or group in the `setup()` method of its containing group:

```python
class MyGroupConfig(df.Config):
  ...

class MyGroup(df.Config):
  config: MyGroupConfig
  MY_NODE: MyNode

  def setup(self) -> None:
    # Cascade config to MY_NODE based on the
    # group's config
    my_node_config = MyNodeConfig(...)
    self.MY_NODE.configure(my_node_config)
```
The exception to this is graphs, which we can construct and configure directly:

```python
my_graph = MyGraph()
my_graph.configure(MyGraphConfig(...))
```
Rather than hard-coding the top-level configuration like this, though, we can automatically build the configuration from from command-line arguments like so:

```python
my_config = MyGraphConfig.fromargs()
```
The `df.run` function actually gets configuration using `fromargs()`, so we can also just run a graph using command-line arguments like so:

```python
df.run(MyGraph)
```
