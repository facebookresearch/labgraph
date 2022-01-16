# LabGraphViz

LabGraphViz provides some useful visualizations for use with labgraph.

## Quick Start

### Method 1 - building from source code

**Prerequisites**:

Make sure to install labgraph before proceeding

```
cd labgraph/extensions/labgraph_viz
python setup.py install
python setup.py sdist bdist_wheel
```

### Testing:

To make sure things are working you can run any of the following examples

```
python -m extensions.labgraph_viz.labgraph_viz.application_example
python -m extensions.labgraph_viz.labgraph_viz.bar_plot_example
python -m extensions.labgraph_viz.labgraph_viz.heat_map_example
python -m extensions.labgraph_viz.labgraph_viz.line_plot_example
python -m extensions.labgraph_viz.labgraph_viz.scatter_plot_example
python -m extensions.labgraph_viz.labgraph_viz.spatial_plot_example
```

### Contributers:
Ryan Catoen, Pradeep Damodara, John Princen, Dev Chakraborty
