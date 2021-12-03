# YAML SUPPORT

yaml_support provides a LabgraphUnits-YAML parser, that's able
to read a python file, identify the different LabgraphUnit and 
serialze them into YAML.

## Quick Start

### Method 1 - building from source code

**Prerequisites**:

Make sure to install labgraph before proceeding

```
cd labgraph/extensions/yaml_support
python setup.py install
```

### Testing:

To make sure things are working you can run

```
python -m extensions.yaml_support.yaml_support.tests.test_lg_yaml_ap
```

