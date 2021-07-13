# LabGraph

LabGraph is a streaming framework built by the Facebook Reality Labs Research team at Facebook.

## Quick Start

**Prerequisites**:

- [Buck](https://buck.build/setup/getting_started.html) ([Watchman](https://facebook.github.io/watchman/docs/install) also recommended)
- [Python 3.6](https://www.python.org/downloads/release/python-368/) (note: currently incompatible with Anaconda)
- **Windows only:** [Build Tools for Visual Studio 2019](https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2019)

**Setup**:

*On Windows, this setup step must be run in "x64 Native Tools Command Prompt for VS 2019" so that we can access the Visual Studio compiler toolchain.*

```
cd labgraph
python setup.py install
```

To make sure things are working you can run the example:

```
python -m labgraph.examples.simple_viz
```

You can also run the test suite as follows:

```
python -m pytest --pyargs labgraph
```

Now go to the [documentation](docs/) to learn more!


**License**:
LabGraph is MIT licensed, as found in the LICENSE file.
