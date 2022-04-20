# Graphviz for LabGraph Graphs

This extension provides an API to generate a graphviz visualization of the LabGraph topology.

## Quick Start

### Method 1 - building from source code

**Prerequisites**:

- Python3\
  Supported python version(s)
  _ [Python3.6](https://www.python.org/downloads/)
  _ [Python3.8](https://www.python.org/downloads/) (**RECOMMENDED**)
- Make sure to install [labgraph](https://github.com/facebookresearch/labgraph) before proceeding
- Make sure to install [graphviz](https://graphviz.org/download/) on your main OS before proceeding

```
cd labgraph/extensions/graphviz_support
python setup.py install
```

### Testing:

To make sure things are working:

1- Move to the root of the LabGraph directory:

```
labgraph\extensions\graphviz_support> cd ../..
labgraph>
```

2- Run the following test

```
python -m extensions.graphviz_support.graphviz_support.tests.test_lg_graphviz_api
```

**The output of the file for this test can be found at:**\
extensions\graphviz_support\graphviz_support\tests\output

### Generating a graphviz file

To generate a graph visualization just call 'generate_graphviz' function and pass the appropriate parameters

```
from graphviz_support import generate_graphviz

generate_graphviz(graph, output_file)
```

### Examples:

To get a better understanding of Graphviz API, please check the following examples

```
python -m extensions.graphviz_support.graphviz_support.examples.simple_viz
```

```
python -m extensions.graphviz_support.graphviz_support.examples.graph_w_logging
```

**(!) The outputs of the above examples can be found under the following folder**
extensions\graphviz_support\graphviz_support\examples\output
