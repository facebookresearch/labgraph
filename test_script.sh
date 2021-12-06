# Copyright 2004-present Facebook. All Rights Reserved.
# RUN export LC_ALL=C.UTF-8
# RUN export LANG=en_US.utf-8

python3.6 -m pytest --pyargs -v labgraph._cthulhu
python3.6 -m pytest --pyargs -v labgraph.events
python3.6 -m pytest --pyargs -v labgraph.graphs
python3.6 -m pytest --pyargs -v labgraph.loggers
python3.6 -m pytest --pyargs -v labgraph.messages
python3.6 -m pytest --pyargs -v labgraph.runners.tests.test_process_manager
python3.6 -m pytest --pyargs -v labgraph.runners.tests.test_aligner
python3.6 -m pytest --pyargs -v labgraph.runners.tests.test_cpp
python3.6 -m pytest --pyargs -v labgraph.runners.tests.test_exception
python3.6 -m pytest --pyargs -v labgraph.runners.tests.test_launch
python3.6 -m pytest --pyargs -v labgraph.runners.tests.test_runner
python3.6 -m pytest --pyargs -v labgraph.zmq_node
python3.6 -m pytest --pyargs -v labgraph.devices.protocols.lsl
