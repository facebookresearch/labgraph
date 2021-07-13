#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

# This is a wrapper around cthulhubindings to randomize the name of the shared memory it
# uses. This allows us to keep shared memory for different LabGraph graphs separate
# when they are running simultaneously.

import os

from ..util.random import random_string

SHM_NAME_ENV_VAR = "CTHULHU_SHM_NAME"
DEFAULT_SHM_NAME = "CthulhuSHM"

# Update the shared memory name to a randomized one if it is the default one or unset
if (
    SHM_NAME_ENV_VAR not in os.environ
    or os.environ[SHM_NAME_ENV_VAR] == DEFAULT_SHM_NAME
):
    SHM_PREFIX = "LABGRAPH_SHMEM_"
    SHM_SUFFIX = random_string(16)
    os.environ[SHM_NAME_ENV_VAR] = f"{SHM_PREFIX}{SHM_SUFFIX}"

import cthulhubindings  # noqa: E402

# TODO (T88919098): For now we manually export items from the bindings to pass
# typechecking (avoiding import *). An improvement would be to generate mypy stubs from
# C++ extensions.
Aligner = cthulhubindings.Aligner
AlignerMode = cthulhubindings.AlignerMode
AnyBuffer = cthulhubindings.AnyBuffer
BufferType = cthulhubindings.BufferType
Clock = cthulhubindings.Clock
ClockAuthority = cthulhubindings.ClockAuthority
ClockEvent = cthulhubindings.ClockEvent
clockManager = cthulhubindings.clockManager
ClockManager = cthulhubindings.ClockManager
ContextInfo = cthulhubindings.ContextInfo
ControllableClock = cthulhubindings.ControllableClock
CpuBuffer = cthulhubindings.CpuBuffer
DynamicParameters = cthulhubindings.DynamicParameters
Field = cthulhubindings.Field
GpuBuffer = cthulhubindings.GpuBuffer
ImageBuffer = cthulhubindings.ImageBuffer
memoryPool = cthulhubindings.memoryPool
MemoryPool = cthulhubindings.MemoryPool
PerformanceSummary = cthulhubindings.PerformanceSummary
SampleHeader = cthulhubindings.SampleHeader
SampleMetadata = cthulhubindings.SampleMetadata
StreamConfig = cthulhubindings.StreamConfig
StreamConsumer = cthulhubindings.StreamConsumer
StreamDescription = cthulhubindings.StreamDescription
StreamInterface = cthulhubindings.StreamInterface
StreamProducer = cthulhubindings.StreamProducer
streamRegistry = cthulhubindings.streamRegistry
StreamRegistry = cthulhubindings.StreamRegistry
StreamSample = cthulhubindings.StreamSample
ThreadPolicy = cthulhubindings.ThreadPolicy
TypeDefinition = cthulhubindings.TypeDefinition
TypeInfo = cthulhubindings.TypeInfo
typeRegistry = cthulhubindings.typeRegistry
TypeRegistry = cthulhubindings.TypeRegistry
