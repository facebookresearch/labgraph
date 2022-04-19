# MacOS Installation Guide

Before installing LabGraph, make sure you have the correct version of Python installed. LabGraph is supported on Python3.6+ for MacOS, and Python3.8 is recommended.

Install a standalone [Python](https://www.python.org/downloads/) and make it the default Python version.

## Troubleshoot for Python3.8 (MacOS Monterey and Big Sur): 
----

If the following error appears when importing LabGraph:
```
ImportError: Library not loaded: /usr/local/opt/python@3.8/Frameworks/Python.framework/Versions/3.8/Python
Reason: tried: '/usr/local/opt/python@3.8/Frameworks/Python.framework/Versions/3.8/Python' (no such file), '/Library/Frameworks/Python.framework/Versions/3.8/Python' (no such file), '/System/Library/Frameworks/Python.framework/Versions/3.8/Python' (no such file)
```

Make sure the newly installed Python is linked as the default Python version on your Mac.

If you installed Python3.8 using `brew` and want to make it the default Python version, you can use the following instructions: 

- Add the path/to/your/Python3.8 to the top of the PATH variable:
```
echo 'export PATH="/usr/local/opt/python@3.8/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
``` 

- If existing symlinks belong to the system installed Python directory, unlink them and link `python3` to the newly installed Python3.8 directory:
```
unlink /usr/local/bin/python3
ln -s /usr/local/opt/python@3.8/bin/python3 /usr/local/bin/python3
```

- Install LabGraph using PyPI:
```
python3 -m pip install labgraph=2.0.0
```
