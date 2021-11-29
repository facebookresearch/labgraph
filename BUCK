load("//:DEFS", "PLATFORM")

cthulhu_srcs = [
    "Cthulhu/src/Aligner.cpp",
    "Cthulhu/src/AlignerMeta.cpp",
    "Cthulhu/src/BufferTypes.cpp",
    "Cthulhu/src/Clock.cpp",
    "Cthulhu/src/Context.cpp",
    "Cthulhu/src/Dispatcher.cpp",
    "Cthulhu/src/MemoryPoolLocalImpl.cpp",
    "Cthulhu/src/QueueingAligner.cpp",
    "Cthulhu/src/PerformanceMonitor.cpp",
    "Cthulhu/src/PoolGPUAllocator.cpp",
    "Cthulhu/src/RawDynamic.cpp",
    "Cthulhu/src/Serialization.cpp",
    "Cthulhu/src/StreamConfigEquality.cpp",
    "Cthulhu/src/StreamInterface.cpp",
    "Cthulhu/src/StreamType.cpp",
    "Cthulhu/src/SubAligner.cpp",
    "Cthulhu/src/SubAlignerImpl.cpp",
    "Cthulhu/src/TypeHelpers.cpp",
]

cthulhu_public_hdrs = [
    "Cthulhu/include/cthulhu/Aligner.h",
    "Cthulhu/include/cthulhu/AlignerMeta.h",
    "Cthulhu/include/cthulhu/BufferTypes.h",
    "Cthulhu/include/cthulhu/Clock.h",
    "Cthulhu/include/cthulhu/ClockManagerInterface.h",
    "Cthulhu/include/cthulhu/Context.h",
    "Cthulhu/include/cthulhu/ContextImpl.h",
    "Cthulhu/include/cthulhu/ContextImpl_details.h",
    "Cthulhu/include/cthulhu/ContextRegistryInterface.h",
    "Cthulhu/include/cthulhu/Dispatcher.h",
    "Cthulhu/include/cthulhu/FieldData.h",
    "Cthulhu/include/cthulhu/ForceCleanable.h",
    "Cthulhu/include/cthulhu/Framework.h",
    "Cthulhu/include/cthulhu/FrameworkBase.h",
    "Cthulhu/include/cthulhu/LogDisabling.h",
    "Cthulhu/include/cthulhu/MemoryPoolInterface.h",
    "Cthulhu/include/cthulhu/PerformanceMonitor.h",
    "Cthulhu/include/cthulhu/QueueingAligner.h",
    "Cthulhu/include/cthulhu/RawDynamic.h",
    "Cthulhu/include/cthulhu/Serialization.h",
    "Cthulhu/include/cthulhu/StreamConfigEquality.h",
    "Cthulhu/include/cthulhu/StreamInterface.h",
    "Cthulhu/include/cthulhu/StreamRegistryInterface.h",
    "Cthulhu/include/cthulhu/StreamType.h",
    "Cthulhu/include/cthulhu/SubAligner.h",
    "Cthulhu/include/cthulhu/TypeHelpers.h",
    "Cthulhu/include/cthulhu/TypeRegistryInterface.h",
    "Cthulhu/include/cthulhu/VulkanUtil.h",
]

cxx_library(
    name="CthulhuCore",
    preferred_linkage="static",
    srcs=cthulhu_srcs,
    public_include_directories=["Cthulhu/include"],
    exported_headers=cthulhu_public_hdrs,
    deps=[
        "//logging:logging",
        "//third-party/boost:boost",
    ],
    link_whole=True,
    visibility=["PUBLIC"],
)

cxx_library(
    name="CthulhuVulkanUtilStub",
    preferred_linkage="static",
    srcs=["Cthulhu/src/VulkanUtil.cpp"],
    deps=[":CthulhuCore"],
)

cthulhu_private_local_hdrs = [
    "Cthulhu/src/ClockLocal.h",
    "Cthulhu/src/ClockManagerLocal.h",
    "Cthulhu/src/ContextRegistryLocal.h",
    "Cthulhu/src/MemoryPoolLocal.h",
    "Cthulhu/src/StreamRegistryLocal.h",
    "Cthulhu/src/TypeRegistryLocal.h",
]

cthulhu_local_srcs = [
    "Cthulhu/src/ClockLocal.cpp",
    "Cthulhu/src/ClockManagerLocal.cpp",
    "Cthulhu/src/ContextRegistryLocal.cpp",
    "Cthulhu/src/MemoryPoolLocal.cpp",
    "Cthulhu/src/StreamRegistryLocal.cpp",
    "Cthulhu/src/TypeRegistryLocal.cpp",
]

cxx_library(
    name="CthulhuLocalComponents",
    preferred_linkage="static",
    srcs=cthulhu_local_srcs,
    public_include_directories=["Cthulhu/include"],
    link_whole=True,
    raw_headers=cthulhu_private_local_hdrs,
    deps=[":CthulhuCore", ":CthulhuVulkanUtilStub"],
)

cthulhu_private_ipc_hdrs = [
    "Cthulhu/src/AuditorIPC.h",
    "Cthulhu/src/ClockIPC.h",
    "Cthulhu/src/ClockManagerIPC.h",
    "Cthulhu/src/ContextRegistryIPC.h",
    "Cthulhu/src/IPCEssentials.h",
    "Cthulhu/src/MemoryPoolIPC.h",
    "Cthulhu/src/MemoryPoolIPCHybrid.h",
    "Cthulhu/src/StreamInterfaceIPC.h",
    "Cthulhu/src/StreamRegistryIPC.h",
    "Cthulhu/src/StreamRegistryIPCHybrid.h",
    "Cthulhu/src/TypeRegistryIPC.h",
    "Cthulhu/src/boost/interprocess/android_shared_memory.hpp",
    "Cthulhu/src/boost/interprocess/managed_android_shared_memory.hpp",
    "Cthulhu/src/boost/interprocess/detail/managed_open_or_create_impl_ashmem.hpp",
]

cthulhu_ipc_srcs = [
    "Cthulhu/src/AuditorIPC.cpp",
    "Cthulhu/src/ClockIPC.cpp",
    "Cthulhu/src/ClockManagerIPC.cpp",
    "Cthulhu/src/ContextRegistryIPC.cpp",
    "Cthulhu/src/FrameworkIPCHybrid.cpp",
    "Cthulhu/src/MemoryPoolIPC.cpp",
    "Cthulhu/src/MemoryPoolIPCHybrid.cpp",
    "Cthulhu/src/StreamInterfaceIPC.cpp",
    "Cthulhu/src/StreamRegistryIPCHybrid.cpp",
    "Cthulhu/src/TypeRegistryIPC.cpp",
]

cxx_library(
    name="CthulhuIPCHybridBase",
    preferred_linkage="static",
    srcs=cthulhu_ipc_srcs,
    include_directories=["Cthulhu"],
    link_whole=True,
    exported_preprocessor_flags=["-DCTHULHU_FRAMEWORK_IPCHYBRID"],
    raw_headers=cthulhu_private_ipc_hdrs,
    deps=[
        ":CthulhuCore",
        ":CthulhuLocalComponents",
        "//third-party/boost:boost",
        "//third-party/boost:boost_date_time",
        "//third-party/boost:boost_thread",
    ],
)

cxx_library(
    name="CthulhuIPCHybrid",
    preferred_linkage="static",
    link_whole=True,
    srcs=[
        "Cthulhu/src/FrameworkInstance.cpp",
    ],
    exported_linker_flags={
        "linux": ["-lrt", "-lpthread"],
        "win": ["/IGNORE:4217"],
    }.get(PLATFORM, []),
    deps=[":CthulhuIPCHybridBase"],
    visibility=["PUBLIC"],
)

cxx_library(
    name="bindings_core",
    preferred_linkage="static",
    srcs=[
        "Cthulhu/modules/pythonbindings/core.cpp",
        "Cthulhu/modules/pythonbindings/cuda_util.cpp",
    ],
    public_include_directories=["Cthulhu/modules/pythonbindings/include"],
    raw_headers=[
        "Cthulhu/modules/pythonbindings/include/cthulhu/bindings/core.h",
        "Cthulhu/modules/pythonbindings/include/cthulhu/bindings/cuda_util.h",
    ],
    deps=[
        ":CthulhuCore",
        "//third-party/pybind11:pybind11",
    ],
)

cxx_library(
    name="cthulhubindings",
    preferred_linkage="shared",
    srcs=["Cthulhu/modules/pythonbindings/module.cpp"],
    compiler_flags=["-fvisibility=hidden", "-DCTHULHU_EXTERNAL=1"],
    deps=[
        ":bindings_core",
        ":CthulhuIPCHybrid",
        "//third-party/pybind11:pybind11",
    ],
)

cxx_library(
    name="labgraph_cpp",
    preferred_linkage="static",
    srcs=[
        "labgraph/cpp/Node.cpp",
    ],
    public_include_directories=["labgraph/cpp/include"],
    exported_headers=[
        "labgraph/cpp/include/labgraph/bindings.h",
        "labgraph/cpp/include/labgraph/Node.h",
        "labgraph/cpp/include/labgraph/NodeImpl.h",
    ],
    deps=[
        ":CthulhuCore",
        "//third-party/pybind11:pybind11",
    ],
    link_whole=True,
    visibility=["PUBLIC"],
)

cxx_library(
    name="labgraph_cpp_bindings",
    preferred_linkage="shared",
    srcs=["labgraph/cpp/bindings.cpp"],
    public_include_directories=["labgraph/cpp/include"],
    exported_headers=[
        "labgraph/cpp/include/labgraph/bindings.h",
    ],
    deps=[
        "//third-party/pybind11:pybind11",
        ":labgraph_cpp",
        ":CthulhuIPCHybrid",
    ],
    link_style="static" if PLATFORM == "win" else "static_pic",
    visibility=["PUBLIC"],
    compiler_flags=["-fvisibility=hidden"],
    soname="labgraph_cpp.$(ext)",
)

cxx_library(
    name="MyCPPNodes",
    srcs=[
        "labgraph/cpp/tests/MyCPPSink.cpp",
        "labgraph/cpp/tests/MyCPPSource.cpp",
        "labgraph/cpp/tests/bindings.cpp",
    ],
    headers=[
        "labgraph/cpp/tests/MyCPPSink.h",
        "labgraph/cpp/tests/MyCPPSource.h",
        "labgraph/cpp/tests/TestSample.h",
    ],
    deps=[
        ":labgraph_cpp",
        ":CthulhuCore",
        ":CthulhuIPCHybrid",
        "//third-party/pybind11:pybind11",
    ],
    soname="MyCPPNodes.$(ext)",
    compiler_flags=["-fvisibility=hidden"],
    link_style="static" if PLATFORM == "win" else "static_pic",
)

cxx_binary(
    name="CthulhuIPCClean",
    srcs=["Cthulhu/ipc_cleanup.cpp"],
    deps=[":CthulhuIPCHybrid"],
)
