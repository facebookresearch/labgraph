# Graphviz for LabGraph graphs

This extension provides an API to generate a graphviz visualization of the LabGraph topology. 

## Quick Start

### Method 1 - building from source code

**Prerequisites**:
* Python3\
Supported python version(s)
    * [Python3.6](https://www.python.org/downloads/)
    * [Python3.8](https://www.python.org/downloads/) (**RECOMMENDED**)
* Make sure to install [labgraph](https://github.com/facebookresearch/labgraph) before proceeding
* Make sure to install [graphviz](https://graphviz.org/download/) on your main OS before proceeding

```
cd labgraph/extensions/graphviz_support
python setup.py install
```

### Testing:

To make sure things are working you can run any of the following examples

```
python -m extensions.graphviz_support.graphviz_support.tests.test_lg_graphviz_api
```

### Generating a graphviz file

To generate a graph visualization just call 'generate_graphviz' function and pass the appropriate parameters
```
from extensions/graphviz_support/graphviz_support/generate_graphviz/generate_graphviz.py import generate_graphviz.py

generate_graphviz(graph, output_file)
```
