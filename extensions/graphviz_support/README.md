# Graphviz for LabGraph graphs

This extension provides an API to generate a [graphviz](https://graphviz.org/) visualization of the LabGraph topology. 

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

To make sure things are working:

1. Move to the root of the LabGraph directory:

```bash
labgraph/extensions/graphviz_support> cd ../..
labgraph>
```
2. Run the following test

```bash
python -m extensions.graphviz_support.graphviz_support.tests.test_lg_graphviz_api
```

**The output of the file for this test can be found at:**

`extensions/graphviz_support/graphviz_support/tests/output/test.svg`

### Generating a graphviz file

To generate a graph visualization just call 'generate_graphviz' function and pass the appropriate parameters

```python
from extensions.graphviz_support.graphviz_support.generate_graphviz.generate_graphviz import generate_graphviz
from extensions.graphviz_support.graphviz_support.tests.demo_graph.demo import Demo

generate_graphviz(Demo(), "output.png") # you can also use "output.svg"
```

**It will produce the following diagram named `output.png` in your current directory:**

![Graphviz diagram for nodes: RollingAverager, NoiseGenerator, Amplifier, Sink, and Attenuator](https://i.imgur.com/M4yL39x.png)
