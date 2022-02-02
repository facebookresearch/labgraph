# MacOS Installation Guide

Before installing LabGraph, make sure you have the correct version of Python installed. LabGraph is supported on Python3.6+ for MacOS, and Python3.8 is recommended.

Install a standalone [Python](https://www.python.org/downloads/) and make it the default Python version.

## Troubleshoot for Python3.8 (MacOS Monterey and Big Sur): 

If you installed Python3.8 using `brew` and want to make it the default Python version, add the link to `python@3.8` to the top of the PATH variable:
```
echo 'export PATH="/usr/local/opt/python@3.8/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
``` 

If exististing symlinks belong to the system installed Python directory, unlink them and link `python3` to the newly installed Python:
```
unlink /usr/local/bin/python3
ln -s /usr/local/opt/python@3.8/bin/python3 /usr/local/bin/python3
```

Install LabGraph using PyPI:
```
python3 -m pip install labgraph=2.0.0
```
