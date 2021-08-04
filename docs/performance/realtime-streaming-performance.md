# Real-Time Streaming Performance in LabGraph & Cthulhu

TL;DR: Based on a performance test in this doc, LabGraph and Cthulhu support 100s of MB/s of data transfer in several kHz of samples.

## Plots

![Sample Rate and Data Transfer cross Platfrom and Language](https://raw.githubusercontent.com/facebookresearch/labgraph/master/docs/performance/images/sample_rate_data_transfer_cross_platform_language.png)

![Sample Rate and Data Transfer by Block Size](https://raw.githubusercontent.com/facebookresearch/labgraph/master/docs/performance/images/sample_rate_data_transfer_rate_by_block_size.png)

<p align="center">
   <img width="460*2" height="300*2" src="https://raw.githubusercontent.com/facebookresearch/labgraph/master/docs/performance/images/sample_latency.png">
</p>

## Discussion

* The difference between C++ and Python performance is not as large in this analysis. There is still a significant scalar difference on macOS and Linux, but it likely leaves many high-throughput use cases on the table for use with Python.
* In a few cases (Windows sample rate, macOS data rate), the Python performance is actually *greater* than the C++ performance! The way we allocate samples in Python and C++ follow fairly different code paths, so it may be the case that the C++ test is incurring some overhead that the Python test isn’t. One difference between the two is that the C++ test makes use of a subclass of `cthulhu::AutoStreamSample` whereas Python always stays at the more generic `cthulhu::StreamSample` level. Another difference is that Python uses numpy to deal with blocks whereas C++ doesn’t. However, a deeper analysis will help to get to the bottom of this.
* In this study, data rate we can achieve generally plateaus around a 2 MB block size; beyond this point the cost of constructing and reading the blocks presumably outpaces the gains from a larger block.
* In C++, the sample rate on Windows is a lot slower than on macOS and Linux, which may be explained by the signalling mechanism used by Boost::Interprocess on Windows.

## Methodology
* The root process decides the number of tests to run, and their parameters, based on command-line arguments. In particular, because we are interested in the effect of the block size, there is a --dynamic-size parameter which selects a single chosen dynamic block size, or --many-dynamic-sizes which runs many tests for a battery of different dynamic block sizes. For this analysis a log scale from 2^3 to 2^23 bytes is used for the block sizes. The --duration parameter controls how long each block size is streamed for; 2 minutes (--duration 120) are chosen.
* These tests often provide variable results because of the OS’s scheduler, which can technically put the test to sleep for as long as it wants. To minimize this variability tools of the OSes are used to maximize the priority given to the root process (this priority then cascades to the child processes we spawn). For macOS and Linux this meant the load test is run with sudo nice -n -20 and on Windows start /realtime is used.
* For each test, a publisher process and a subscriber process are started. The publisher process creates a stream and starts publishing samples to it as quickly as the CPU allows (i.e., the publisher doesn’t try to sleep between samples). The subscriber subscribes to the stream and logs some minimal timing information for each sample received.
* Once the specified duration has elapsed, the publisher and subscriber shut down. Each process logs some statistics, and also writes statistics to an HDF5 file. Each HDF5 file is uploaded to notebook for further analysis and the plots you see here.

## Caveats & Opportunities
* These results are only as good as the tests. As mentioned above, some discrepancy between the C++ and Python versions of the load test is making it so that Python sometimes outperforms C++. This could be pointing to either a mistake in the load test implementation adding extra overhead to C++. It could also be the case that the code paths in these cases are so different that the performance really does turn out this way.
* In these tests a very simple graph topology is used: one publisher streaming to one subscriber. More sophisticated graph topologies with many publishers and/or subscribers could be tested.
* Only the low-level transport is tested here, but there are many common real-time algorithms we will wish to profile and tune as well. For example, we will want stream alignment to be about as performant as the transport.
* These results are subject to the state of the overall machine, which can change over time. These results change somewhat upon repeated runs. This could be dealt with a little bit by extending the length of the test. (the duration is kept to 2 minutes for now because this is already a 42-minute test for the 21 block size options.)
* The hardware used likely contributes significantly to these results. For this analysis, a 2017 Macbook Pro, a Razer Full HD, and a 57 GB RAM machine running CentOS.
* Beyond hardware, there may be operating system differences in performance, such as the signalling performance issue on Windows discussed above.
* IPC backend in Cthulhu is checked which uses Boost::Interprocess to signal between multiple processes, and is the most common use case in LabGraph. It is also possible to use the Local backend, which is expected to produce performance results far superior to what is seen here since interprocess signalling is likely what bottlenecks the sample rate.
* The overhead in the subscriber process is tried to minimized upon receiving a sample, but there may be some remaining overhead.

## Overall Takeaways
* This study provides a high level picture of how LabGraph and Cthulhu perform on different platforms. What we can see for sure is that the order of magnitude we are dealing with is several kHz of samples and 100s of MB/s of data transfer that Dragonfly can support. The uncertainty comes from the tests that were written, in particular when we try to compare across languages. Still, from speaking with our colleagues in Pittsburgh who work on Cthulhu, it sounds like this is a reasonable starting point for understanding our performance that we can build upon. For example, we can take these metrics, start logging them, and monitor for regressions; even if the metrics aren’t perfect, sudden movements in them could alert us to potentially faulty changes. This also gives us a reasonable ballpark for whether or not we would be able to support the data rate of a proposed hardware system.
* Please share your thoughts and suggestions! Measuring and tuning the performance of our frameworks is a work in progress. Additional ideas for testing methods and analyses are welcomed.

More details on the analysis can be found [here](https://github.com/facebookresearch/labgraph/tree/master/docs/performance).
Sample test run: python load_test.py --duration 30 --output load_test.h5
