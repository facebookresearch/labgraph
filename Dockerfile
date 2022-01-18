#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

FROM quay.io/pypa/manylinux2014_x86_64

# Install devtoolset-9
RUN yum update -y
RUN yum install -y centos-release-scl
RUN yum install -y devtoolset-9
RUN echo "source /opt/rh/devtoolset-9/enable" >> /etc/bashrc
SHELL ["/bin/bash", "--login", "-c"]
RUN g++ --version

# Install Python, Java, wget, vim
RUN yum install -y python2 python3 python3-devel wget java-1.8.0-openjdk \
    java-1.8.0-openjdk-devel vim

# Install Ant
WORKDIR "/tmp"
RUN wget https://downloads.apache.org/ant/binaries/apache-ant-1.10.11-bin.zip
RUN unzip apache-ant-1.10.11-bin.zip \
    && mv apache-ant-1.10.11/ /opt/ant \
    && ln -s /opt/ant/bin/ant /usr/bin/ant

# Download Buck
WORKDIR "/opt"
RUN git clone https://github.com/facebook/buck.git

# Set JAVA_HOME
ENV JAVA_HOME="/usr/lib/jvm/java-1.8.0-openjdk"

# Build Buck
WORKDIR "/opt/buck"
RUN ant
RUN ln -s /opt/buck/bin/buck /usr/bin/buck

# Install Watchman
WORKDIR "/opt/watchman"
RUN wget https://github.com/facebook/watchman/releases/download/v2020.09.21.00/watchman-v2020.09.21.00-linux.zip
RUN unzip watchman-v2020.09.21.00-linux.zip
WORKDIR "/opt/watchman/watchman-v2020.09.21.00-linux"
RUN mkdir -p /usr/local/{bin,lib} /usr/local/var/run/watchman
RUN cp bin/* /usr/local/bin
RUN cp lib/* /usr/local/lib
RUN chmod 755 /usr/local/bin/watchman
RUN chmod 2777 /usr/local/var/run/watchman

# Unpack the static python libraries from the manylinux image.
WORKDIR "/opt/_internal/"
RUN XZ_OPT=-9e tar -xf static-libs-for-embedding-only.tar.xz cpython-*/lib/libpython*.a

# Copy LabGraph files
WORKDIR "/opt/labgraph/"

# Copy labgraph into the container
COPY . .

# Create a user to act as the builder.
# This is done to prevent root installs with pip.
RUN useradd -m -r builder && \
    chown -R builder /opt/labgraph
USER builder

# Build LabGraph Wheel
RUN python3.6 -m pip install build && \
 python3.6 -m build --sdist --wheel 
# Build LabGraph Wheel
RUN sed -i 's/3.6/3.7/' /opt/labgraph/third-party/python/DEFS && \
 python3.7 -m pip install build && \
 python3.7 -m build --sdist --wheel 
# Build LabGraph Wheel
RUN sed -i 's/3.7/3.8/' /opt/labgraph/third-party/python/DEFS && \
 python3.8 -m pip install build && \
 python3.8 -m build --sdist --wheel
# Build LabGraph Wheel
RUN sed -i 's/3.8/3.9/' /opt/labgraph/third-party/python/DEFS && \
 python3.9 -m pip install build && \
 python3.9 -m build --sdist --wheel
# Build LabGraph Wheel
RUN sed -i 's/3.9/3.10/' /opt/labgraph/third-party/python/DEFS && \
 python3.10 -m pip install build && \
 python3.10 -m build --sdist --wheel --no-isolation

# Build wheels for each python version
RUN find dist/*whl -exec auditwheel repair {} -w dist/ \;

# Test LabGraph for python3.6
RUN python3.6 -m pip install \
 dist/labgraph-2.0.0-cp36-cp36m-manylinux_2_17_x86_64.manylinux2014_x86_64.whl && \
 python3.6 -m pytest --pyargs -v labgraph._cthulhu && \
 python3.6 -m pytest --pyargs -v labgraph.events && \
 python3.6 -m pytest --pyargs -v labgraph.graphs && \
 python3.6 -m pytest --pyargs -v labgraph.loggers && \
 python3.6 -m pytest --pyargs -v labgraph.messages && \
 python3.6 -m pytest --pyargs -v labgraph.runners.tests.test_process_manager && \
 python3.6 -m pytest --pyargs -v labgraph.runners.tests.test_aligner && \
 python3.6 -m pytest --pyargs -v labgraph.runners.tests.test_cpp && \
 python3.6 -m pytest --pyargs -v labgraph.runners.tests.test_exception && \
 python3.6 -m pytest --pyargs -v labgraph.runners.tests.test_launch && \
 python3.6 -m pytest --pyargs -v labgraph.runners.tests.test_runner

# Test LabGraph for python3.7
RUN python3.7 -m pip install \
 dist/labgraph-2.0.0-cp37-cp37m-manylinux_2_17_x86_64.manylinux2014_x86_64.whl && \
 python3.7 -m pytest --pyargs -v labgraph._cthulhu && \
 python3.7 -m pytest --pyargs -v labgraph.events && \
 python3.7 -m pytest --pyargs -v labgraph.graphs && \
 python3.7 -m pytest --pyargs -v labgraph.loggers && \
 python3.7 -m pytest --pyargs -v labgraph.messages && \
 python3.7 -m pytest --pyargs -v labgraph.runners.tests.test_process_manager && \
 python3.7 -m pytest --pyargs -v labgraph.runners.tests.test_aligner && \
 python3.7 -m pytest --pyargs -v labgraph.runners.tests.test_cpp && \
 python3.7 -m pytest --pyargs -v labgraph.runners.tests.test_exception && \
 python3.7 -m pytest --pyargs -v labgraph.runners.tests.test_launch && \
 python3.7 -m pytest --pyargs -v labgraph.runners.tests.test_runner

# Test LabGraph for python3.8
RUN python3.8 -m pip install \
 dist/labgraph-2.0.0-cp38-cp38-manylinux_2_17_x86_64.manylinux2014_x86_64.whl && \
 python3.8 -m pytest --pyargs -v labgraph._cthulhu && \
 python3.8 -m pytest --pyargs -v labgraph.events && \
 python3.8 -m pytest --pyargs -v labgraph.graphs && \
 python3.8 -m pytest --pyargs -v labgraph.loggers && \
 python3.8 -m pytest --pyargs -v labgraph.messages && \
 python3.8 -m pytest --pyargs -v labgraph.runners.tests.test_process_manager && \
 python3.8 -m pytest --pyargs -v labgraph.runners.tests.test_aligner && \
 python3.8 -m pytest --pyargs -v labgraph.runners.tests.test_cpp && \
 python3.8 -m pytest --pyargs -v labgraph.runners.tests.test_exception && \
 python3.8 -m pytest --pyargs -v labgraph.runners.tests.test_launch && \
 python3.8 -m pytest --pyargs -v labgraph.runners.tests.test_runner

# Test LabGraph for python3.9
RUN python3.9 -m pip install \
 dist/labgraph-2.0.0-cp39-cp39-manylinux_2_17_x86_64.manylinux2014_x86_64.whl && \
 python3.9 -m pytest --pyargs -v labgraph._cthulhu && \
 python3.9 -m pytest --pyargs -v labgraph.events && \
 python3.9 -m pytest --pyargs -v labgraph.graphs && \
 python3.9 -m pytest --pyargs -v labgraph.loggers && \
 python3.9 -m pytest --pyargs -v labgraph.messages && \
 python3.9 -m pytest --pyargs -v labgraph.runners.tests.test_process_manager && \
 python3.9 -m pytest --pyargs -v labgraph.runners.tests.test_aligner && \
 python3.9 -m pytest --pyargs -v labgraph.runners.tests.test_cpp && \
 python3.9 -m pytest --pyargs -v labgraph.runners.tests.test_exception && \
 python3.9 -m pytest --pyargs -v labgraph.runners.tests.test_launch && \
 python3.9 -m pytest --pyargs -v labgraph.runners.tests.test_runner

# Test LabGraph for python3.10
RUN python3.10 -m pip install \
 dist/labgraph-2.0.0-cp310-cp310-manylinux_2_17_x86_64.manylinux2014_x86_64.whl && \
 python3.10 -m pytest --pyargs -v labgraph._cthulhu && \
 python3.10 -m pytest --pyargs -v labgraph.events && \
 python3.10 -m pytest --pyargs -v labgraph.graphs && \
 python3.10 -m pytest --pyargs -v labgraph.loggers && \
 python3.10 -m pytest --pyargs -v labgraph.messages && \
 python3.10 -m pytest --pyargs -v labgraph.runners.tests.test_process_manager && \
 python3.10 -m pytest --pyargs -v labgraph.runners.tests.test_aligner && \
 python3.10 -m pytest --pyargs -v labgraph.runners.tests.test_cpp && \
 python3.10 -m pytest --pyargs -v labgraph.runners.tests.test_exception && \
 python3.10 -m pytest --pyargs -v labgraph.runners.tests.test_launch && \
 python3.10 -m pytest --pyargs -v labgraph.runners.tests.test_runner

