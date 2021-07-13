# Introduction

LabGraph is a Python framework for building real-time research systems. The Facebook Reality Lab Research (FRLR) team at Facebook uses it to rapidly prototype and test new wearable hardware systems, experimental stimulus protocols, digital signal processing steps, and live visualizations. LabGraph has allowed FRLR to greatly accelerate its pace of experimentation. We hope for other groups to benefit from this tooling as well.

More specifically, LabGraph provides a way to define a computational graph in a standardized way. This results in a less tedious development process for real-time algorithms and systems. In other words, the framework decides how data types, computations, and connections between the inputs and outputs of related computations should be stated, and then it sets up the boilerplate needed to run these streaming computations efficiently in parallel. In turn, the researcher is able to focus on developing individual real-time algorithms while assuming the rest of the system runs correctly.

We built LabGraph because there was no existing solution that we felt was sufficiently user-friendly, performant, and flexible. Our primary goal was to minimize the time it takes for a scientist to get from an idea to an experiment. In addition, we wanted to support the high data rates (several MHz) that might come from certain sensors. Also, we wanted to make it easy to extract algorithms from existing projects for reuse in new ones.

## Features

LabGraph comes with built-in support for the following:

* **Performant real-time streaming:** LabGraph depends on Cthulhu (a C++ framework for real-time streaming. The Facebook Reality Lab in Pittsburgh has used this framework to stream high data rates (on the order of MHz), and with LabGraph we are adapting it to work with  hardware. In particular Cthulhu uses shared memory to minimize copies and buffer recycling to minimize allocations.
* **Graph API:** LabGraph allows us to define computational graphs as Python classes. Each LabGraph graph describes a real-time system that includes "nodes" for hardware streaming, signal processing, machine learning, and/or user interfaces. We can also define reusable groups of nodes - each group describes a subsystem that we can reuse in different graphs.
* **Data logging:** A logger for the HDF5 disk format comes built-in, and additional formats can be implemented using a Logger abstraction. The data types used in streams and on disk are derived from Messages, which are an extension of dataclasses; creating and updating these types is as easy as working with dataclasses.
* **Python-C++ interoperability:** LabGraph allows nodes to be written in C++, which can be useful in situations where tuning the performance of an algorithm in Python would be too difficult. Using pybind11, C++ nodes can be dropped into LabGraph graphs as if they were Python nodes. For more flexibility (but at the cost of access to LabGraph features), it is also possible to write C++ that interacts directly with the Cthulhu transport framework.
* **Stimulus events:** We can write "event generators" to define the stimulus events that will occur in an experiment. This serves as a useful abstraction for the current state of the experiment.
* **Parallelism in Python:** Writing parallel Python code is notoriously difficult. LabGraph helps ease some of this difficulty with a) a process manager that takes care of spawning and monitoring parallel processes, and b) asyncio support for concurrency within each process.

## Opinions

The development of LabGraph has been motivated by the following beliefs:

1. **Modularization is critical to building many reliable experimental systems.** Modularization is not the fastest way to build a single system, but it is essential when building many. By doing so, we build a library of well-tested components with behavior that can be isolated from any other part of the system. This keeps the debugging of complex systems tractable and also allows us to write good unit tests.
2. **Python is the language of choice for closed-loop research.** The Python ecosystem is uniquely well-positioned to support decoding efforts: we have access to sophisticated tools for numerical computation and machine learning, as well as a plethora of other well-tested software for working with hardware and UIs. As a result, LabGraph is a Python-first framework.
3. **We need a better way to transition between real-time and analysis work.** The search for the answer to this question has motivated many of our design decisions in LabGraph to date, although so far LabGraph has remained a real-time-only framework. We are just now starting to propose and implement the first designs for using LabGraph graphs & data in an "offline" analysis context. When we are done with this effort we expect to greatly accelerate our cycles of analysis, development, and experimentation.

## Team

LabGraph is currently maintained by Jimmy Feng (primary), Pradeep Damodara, Ryan Catoen and Allen Yin. A non-exhaustive but growing list needs to mention: Dev Chakraborty (primary), Pradeep Damodara, Ryan Catoen, Ruben Sethi, Allen Yin, Rudy Sevile, Sho Nakagome, Ryan Orendorff, Anton Vorontsov, Rosemary Le, Ying Yang, Emily Mugler and Steph Naufel.
