# ZMQ Support

LabGraph has two types of nodes which allow us to use the [ZeroMQ (ZMQ) library](https://zeromq.org/languages/python/): `ZMQPollerNode` and `ZMQSenderNode`. They work with ZMQ sockets that use the PUB and SUB modes; other modes like REQ/REP and PAIR are currently unsupported.

## ZMQMessage

The basic message type that is used by both the `ZMQPollerNode` and `ZMQSenderNode` to communicate ZMQ data to the graph. It has just one field, `data`, which contains the raw bytes sent over the ZMQ socket.

## ZMQPollerNode

This node polls ZMQ data of a particular ZMQ topic at a particular read address (both configurable). Any data polled by the node is published as a `ZMQMessage` back to the rest of the graph. This node has the following configuration parameters via `ZMQPollerConfig`:

* `read_addr`: The address through which ZMQ data should be polled.
* `zmq_topic`: The ZMQ topic being polled.
* `poll_time`: How long each iteration of the polling loop should take (in seconds)

## ZMQSenderNode

This node subscribes to a stream of `ZMQMessage`s, and publishes its contents over ZMQ at a configured address/topic. This node has the following configuration parameters via `ZMQSenderConfig`:

* `write_addr`: The address to which ZMQ data should be written.
* `zmq_topic`: The ZMQ topic being written to.
