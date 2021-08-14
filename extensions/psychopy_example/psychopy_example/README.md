# Psychopy Example

Provides example usage of psychopy with labgraph.

## Quick Start

### Method 1 - building from source code

**Prerequisites**:

Make sure to install labgraph before proceeding

```
cd extensions/psychopy_example
python setup.py install
```

#### Install-time issues
1. msgpack install fails, but `numpy requires msgpack`
   - Re-run the install command, installation will continue

2. Missing swig.exe, `No such file or directory`
   - https://stackoverflow.com/questions/44504899/installing-pocketsphinx-python-module-command-swig-exe-failed

### Testing:

To make sure things are working you can run the following example from the labgraph dir:
```
python -m extensions.psychopy_example.psychopy_example
```

### Contributers:
Pradeep Damodara
