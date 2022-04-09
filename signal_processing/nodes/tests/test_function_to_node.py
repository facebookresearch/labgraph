# Copyright 2004-present Facebook. All Rights Reserved.

from dataclasses import dataclass
from textwrap import dedent
from typing import Callable, Optional, Tuple

import labgraph as lg
import pytest
from ..function_to_node import (
    FunctionConfig,
    function_to_node,
    parse_function_annotations,
)


###############################################################################
#             Test parse_function_annotations bad function error cases            #
###############################################################################


def test_var_args_raises() -> None:
    def f(a: int, *args):
        pass

    with pytest.raises(ValueError):
        parse_function_annotations(f)


def test_var_kwargs_raises() -> None:
    def f(a: int, **kwargs):
        pass

    with pytest.raises(ValueError):
        parse_function_annotations(f)


def test_no_function_annotation_raises() -> None:
    def f(a):
        pass

    with pytest.raises(ValueError):
        parse_function_annotations(f)


def test_empty_function_raises() -> None:
    def f():
        pass

    with pytest.raises(ValueError):
        parse_function_annotations(f)


def test_multiple_errors_returned_at_once() -> None:
    def f(a, *args, **kwargs):
        pass

    err_msg = dedent(
        """
      Function `f` argument with name `a` does not have a type annotation. All parameters require a type annotation to convert the function to a Labgraph node using `function_to_node`.
      Function `f` takes in a variable argument parameter named `args`. Functions with variable argument parameters cannot be converted to Labgraph nodes using `function_to_node`.
      Function `f` argument with name `args` does not have a type annotation. All parameters require a type annotation to convert the function to a Labgraph node using `function_to_node`.
      Function `f` takes in a variable keyword argument parameter named `kwargs`. Functions with variable keyword argument parameters cannot be converted to Labgraph nodes using `function_to_node`.
      Function `f` argument with name `kwargs` does not have a type annotation. All parameters require a type annotation to convert the function to a Labgraph node using `function_to_node`."""
    ).strip()

    with pytest.raises(ValueError) as excinfo:
        parse_function_annotations(f)
    assert err_msg == str(excinfo.value)


###############################################################################
#               Test parse_function_annotations gives correct output              #
###############################################################################


def test_no_input_or_output() -> None:
    def f():
        pass

    with pytest.raises(ValueError):
        parse_function_annotations(f)


def test_source() -> None:
    def f() -> str:
        pass

    assert parse_function_annotations(f) == (None, {"sample": str}, False)


def test_sink() -> None:
    def f(a: int) -> None:
        pass

    assert parse_function_annotations(f) == ({"a": int}, None, False)


def test_arity_1() -> None:
    def f(a: int) -> str:
        pass

    assert parse_function_annotations(f) == ({"a": int}, {"sample": str}, False)


def test_arity_2() -> None:
    def f(a: int, b: bool) -> str:
        pass

    assert parse_function_annotations(f) == (
        {"a": int, "b": bool},
        {"sample": str},
        False,
    )


def test_keyword_only_in_message() -> None:
    def f(a: int, *, b: bool) -> str:
        pass

    assert parse_function_annotations(f, keyword_only_in_message=False) == (
        {"a": int},
        {"sample": str},
        False,
    )
    assert parse_function_annotations(f, keyword_only_in_message=True) == (
        {"a": int, "b": bool},
        {"sample": str},
        False,
    )


def test_default_keyword_in_message() -> None:
    def f(a: int, b: bool = True) -> str:
        pass

    assert parse_function_annotations(f, default_keyword_in_message=False) == (
        {"a": int},
        {"sample": str},
        False,
    )
    assert parse_function_annotations(f, default_keyword_in_message=True) == (
        {"a": int, "b": bool},
        {"sample": str},
        False,
    )


def test_default_keyword_in_message_and_keyword_only_in_message() -> None:
    def f(a: int, *, b: bool, c: float = 0.0) -> str:
        pass

    assert parse_function_annotations(
        f, default_keyword_in_message=False, keyword_only_in_message=False
    ) == ({"a": int}, {"sample": str}, False)
    assert parse_function_annotations(
        f, default_keyword_in_message=False, keyword_only_in_message=True
    ) == ({"a": int, "b": bool}, {"sample": str}, False)
    assert parse_function_annotations(
        f, default_keyword_in_message=True, keyword_only_in_message=False
    ) == ({"a": int, "c": float}, {"sample": str}, False)
    assert parse_function_annotations(
        f, default_keyword_in_message=True, keyword_only_in_message=True
    ) == ({"a": int, "b": bool, "c": float}, {"sample": str}, False)


def test_deconstruct_dataclass_return_type() -> None:
    @dataclass
    class A:
        field1: int
        field2: str

    def f(a: int) -> A:
        pass

    assert parse_function_annotations(f, deconstruct_dataclass_return_type=False) == (
        {"a": int},
        {"sample": A},
        False,
    )
    assert parse_function_annotations(f, deconstruct_dataclass_return_type=True) == (
        {"a": int},
        {"field1": int, "field2": str},
        True,
    )


def test_single_return_param_name() -> None:
    def f(a: int) -> str:
        pass

    assert parse_function_annotations(
        f, single_return_param_name="zhu_li_do_the_thing"
    ) == ({"a": int}, {"zhu_li_do_the_thing": str}, False)


###############################################################################
#                Test function_to_node messages match function                #
###############################################################################


def test_no_input_message() -> None:
    def f() -> str:
        pass

    (ArgumentMessage, ReturnMessage, _) = function_to_node(f)

    assert ArgumentMessage is None

    # Can we make an instance of the output message?
    assert ReturnMessage.__annotations__ == {"sample": str}
    ReturnMessage(sample="hello")


def test_no_output_message() -> None:
    def f(a: int):
        pass

    (ArgumentMessage, ReturnMessage, _) = function_to_node(f)

    # Can we make an instance of the input message?
    assert ArgumentMessage.__annotations__ == {"a": int}
    ArgumentMessage(a=0)

    assert ReturnMessage is None


def test_message_arity_1() -> None:
    def f(a: int) -> str:
        pass

    (ArgumentMessage, ReturnMessage, _) = function_to_node(f)

    assert ArgumentMessage.__annotations__ == {"a": int}
    ArgumentMessage(a=0)

    assert ReturnMessage.__annotations__ == {"sample": str}
    ReturnMessage(sample="hello")


def test_message_keyword_only_in_message() -> None:
    def f(a: int, *, b: bool) -> str:
        pass

    # False case
    (ArgumentMessage, ReturnMessage, _) = function_to_node(
        f, keyword_only_in_message=False
    )
    assert ArgumentMessage.__annotations__ == {"a": int}
    ArgumentMessage(a=1)

    assert ReturnMessage.__annotations__ == {"sample": str}
    ReturnMessage(sample="Hello")

    # True case
    (ArgumentMessage, ReturnMessage, _) = function_to_node(
        f, keyword_only_in_message=True
    )
    assert ArgumentMessage.__annotations__ == {"a": int, "b": bool}
    ArgumentMessage(a=1, b=False)

    assert ReturnMessage.__annotations__ == {"sample": str}
    ReturnMessage(sample="Hello")


def test_message_default_keyword_in_message() -> None:
    def f(a: int, b: bool = True) -> str:
        pass

    # False case
    (ArgumentMessage, ReturnMessage, _) = function_to_node(
        f, default_keyword_in_message=False
    )
    assert ArgumentMessage.__annotations__ == {"a": int}
    ArgumentMessage(a=1)

    assert ReturnMessage.__annotations__ == {"sample": str}
    ReturnMessage(sample="Hello")

    # True case
    (ArgumentMessage, ReturnMessage, _) = function_to_node(
        f, default_keyword_in_message=True
    )
    assert ArgumentMessage.__annotations__ == {"a": int, "b": bool}
    ArgumentMessage(a=1, b=False)

    assert ReturnMessage.__annotations__ == {"sample": str}
    ReturnMessage(sample="Hello")


def test_message_default_keyword_in_message_and_keyword_only_in_message() -> None:
    def f(a: int, *, b: bool, c: float = 0.0) -> str:
        pass

    # False, False case
    (ArgumentMessage, ReturnMessage, _) = function_to_node(
        f, default_keyword_in_message=False, keyword_only_in_message=False
    )
    assert ArgumentMessage.__annotations__ == {"a": int}
    ArgumentMessage(a=1)

    assert ReturnMessage.__annotations__ == {"sample": str}
    ReturnMessage(sample="Hello")

    # False, True case
    (ArgumentMessage, ReturnMessage, _) = function_to_node(
        f, default_keyword_in_message=False, keyword_only_in_message=True
    )
    assert ArgumentMessage.__annotations__ == {"a": int, "b": bool}
    ArgumentMessage(a=1, b=False)

    assert ReturnMessage.__annotations__ == {"sample": str}
    ReturnMessage(sample="Hello")

    # True, False case
    (ArgumentMessage, ReturnMessage, _) = function_to_node(
        f, default_keyword_in_message=True, keyword_only_in_message=False
    )
    assert ArgumentMessage.__annotations__ == {"a": int, "c": float}
    ArgumentMessage(a=1, c=0.0)

    assert ReturnMessage.__annotations__ == {"sample": str}
    ReturnMessage(sample="Hello")

    # True, True case
    (ArgumentMessage, ReturnMessage, _) = function_to_node(
        f, default_keyword_in_message=True, keyword_only_in_message=True
    )
    assert ArgumentMessage.__annotations__ == {"a": int, "b": bool, "c": float}
    ArgumentMessage(a=1, b=False, c=0.0)

    assert ReturnMessage.__annotations__ == {"sample": str}
    ReturnMessage(sample="Hello")


# If this is included inside of the function it cannot be pickled.
@dataclass
class A:
    field1: int
    field2: str


def test_output_message_unpacking() -> None:
    def f(a: int) -> A:
        pass

    (_, ReturnMessage, _) = function_to_node(f, deconstruct_dataclass_return_type=False)
    assert ReturnMessage.__annotations__ == {"sample": A}
    ReturnMessage(sample=A(1, "Hello"))

    (_, ReturnMessage, _) = function_to_node(f, deconstruct_dataclass_return_type=True)
    assert ReturnMessage.__annotations__ == {"field1": int, "field2": str}
    ReturnMessage(field1=1, field2="Hello")


def test_message_single_return_param_name() -> None:
    def f(a: int) -> str:
        pass

    (_, ReturnMessage, _) = function_to_node(
        f, single_return_param_name="zhu_li_do_the_thing"
    )

    assert ReturnMessage.__annotations__ == {"zhu_li_do_the_thing": str}
    ReturnMessage(zhu_li_do_the_thing="alright_varrick")


def test_topic_names() -> None:
    def f(a: int) -> str:
        pass

    input_topic_name = "hello"
    output_topic_name = "goodbye"

    (ArgumentMessage, ReturnMessage, FunctionNode) = function_to_node(
        f, argument_topic_name=input_topic_name, return_topic_name=output_topic_name
    )

    input_topic = getattr(FunctionNode, input_topic_name)
    isinstance(input_topic, lg.Topic)
    assert input_topic.message_type is ArgumentMessage

    output_topic = getattr(FunctionNode, output_topic_name)
    isinstance(output_topic, lg.Topic)
    assert output_topic.message_type is ReturnMessage


###############################################################################
#                Test that FunctionNode has correct properties                #
###############################################################################


def test_function_node_has_required_entities() -> None:
    def f(a: int) -> str:
        pass

    (ArgumentMessage, ReturnMessage, FunctionNode) = function_to_node(f)

    input_topic = FunctionNode.INPUT
    isinstance(input_topic, lg.Topic)
    assert input_topic.message_type is ArgumentMessage

    output_topic = FunctionNode.OUTPUT
    isinstance(output_topic, lg.Topic)
    assert output_topic.message_type is ReturnMessage

    assert FunctionNode.__module__ == __name__

    assert callable(FunctionNode.run)

    assert FunctionNode.__annotations__ == {"config": FunctionConfig}


###############################################################################
#                   Test function_to_node(f).run(x) == f(x)                   #
###############################################################################


# We generate a class here to not rely on external changes. Additionally we
# layer the classes to demonstrate that the layers of fields are passed through
# correctly.
class SampledIndexMessage(lg.Message):
    sample_index: int


class SampledFlavorMessage(SampledIndexMessage):
    sample_flavor: str


def test_function_returns_same_after_conversion() -> None:
    """Besides testing that the conversion doesn't change the function, it also
    tests that a base class that is not `lg.Message` has its parameters passed
    through."""

    def f(a: int, *, b: int) -> int:
        return a + b

    # Get the autogenerated node and associated classes
    ArgumentMessage, ReturnMessage, FunctionNode = function_to_node(
        f, base_cls=SampledFlavorMessage
    )

    test_harness = lg.NodeTestHarness(FunctionNode)

    # Check that the output from the node matches the output from the function.
    a = 2
    b = 3
    flavor = "bubblegum"

    with test_harness.get_node(config=FunctionConfig(kwargs={"b": b})) as node:
        msg = ArgumentMessage(sample_index=0, sample_flavor=flavor, a=a)
        node_to_value_msg = lg.run_async(node.run, args=[msg])[0][1]

        assert isinstance(node_to_value_msg, ReturnMessage)
        assert node_to_value_msg.sample == f(a, b=b)
        assert node_to_value_msg.sample_index == 0
        assert node_to_value_msg.sample_flavor == flavor


def test_function_config_overrides_message():
    def f(a: int, *, b: int) -> int:
        return a + b

    # Get the autogenerated node and associated classes
    ArgumentMessage, ReturnMessage, FunctionNode = function_to_node(
        f, keyword_only_in_message=True
    )

    test_harness = lg.NodeTestHarness(FunctionNode)

    # Check that the output from the node matches the output from the function.
    a = 2
    b_message = 3
    b_config = 4

    with test_harness.get_node(config=FunctionConfig(kwargs={"b": b_config})) as node:
        msg = ArgumentMessage(a=a, b=b_message)
        node_to_value_msg = lg.run_async(node.run, args=[msg])[0][1]

        assert isinstance(node_to_value_msg, ReturnMessage)
        assert node_to_value_msg.sample == f(a, b=b_config)


###############################################################################
#                                Run in a graph                               #
###############################################################################

# Source function #############################################################


def generate_source_function() -> Callable[[], int]:
    counter = 0

    def source() -> int:
        nonlocal counter
        counter += 1
        return counter

    return source


_, SourceReturnMessage, SourceFunctionNode = function_to_node(
    generate_source_function(), sleep_time=0.03
)


class SourceConsumer(lg.Node):
    INPUT = lg.Topic(SourceReturnMessage)

    last_count: Optional[int]

    def setup(self):
        self.last_count = None

    @lg.subscriber(INPUT)
    async def run(self, message: SourceReturnMessage):
        if self.last_count is None:
            self.last_count = message.sample - 1
        assert (message.sample - self.last_count) == 1

        self.last_count = message.sample
        if message.sample > 10:
            raise lg.NormalTermination()


class SourceGraph(lg.Graph):
    FUNCTION: SourceFunctionNode
    CONSUMER: SourceConsumer

    def connections(self) -> lg.Connections:
        return ((self.FUNCTION.OUTPUT, self.CONSUMER.INPUT),)

    def process_modules(self) -> Tuple[lg.Module, ...]:
        return (self.FUNCTION, self.CONSUMER)


@pytest.mark.skip(reason="Currently complains of hanging source node")
def test_source_graph() -> None:
    g = SourceGraph()
    runner = lg.ParallelRunner(graph=g)
    runner.run()


# Sink function ###############################################################


def sink(a: int):
    pass


SinkArgumentMessage, _, SinkFunctionNode = function_to_node(sink)


class SinkGenerator(lg.Node):
    OUTPUT = lg.Topic(SinkArgumentMessage)

    counter: int

    def setup(self):
        self.counter = 0

    @lg.publisher(OUTPUT)
    async def run(self) -> lg.AsyncPublisher:
        while True:
            self.counter += 1
            if self.counter > 10:
                raise lg.NormalTermination()

            yield self.OUTPUT, SinkArgumentMessage(a=self.counter)


class SinkGraph(lg.Graph):
    GENERATOR: SinkGenerator
    FUNCTION: SinkFunctionNode

    def connections(self) -> lg.Connections:
        return ((self.GENERATOR.OUTPUT, self.FUNCTION.INPUT),)

    def process_modules(self) -> Tuple[lg.Module, ...]:
        return (self.GENERATOR, self.FUNCTION)


def test_sink_graph() -> None:
    g = SinkGraph()
    runner = lg.ParallelRunner(graph=g)
    runner.run()


# Function that takes and returns a value #####################################


def input_output_function(a: int) -> int:
    return a + 4


(
    InputOutputArgumentMessage,
    InputOutputReturnMessage,
    InputOutputFunctionNode,
) = function_to_node(input_output_function)


class InputOutputGenerator(lg.Node):
    OUTPUT = lg.Topic(InputOutputArgumentMessage)

    counter: int

    def setup(self):
        self.counter = 0

    @lg.publisher(OUTPUT)
    async def run(self) -> lg.AsyncPublisher:
        while self.counter < 10:
            self.counter += 1
            yield self.OUTPUT, InputOutputArgumentMessage(a=self.counter)
        raise lg.NormalTermination()


class InputOutputConsumer(lg.Node):
    INPUT = lg.Topic(InputOutputReturnMessage)

    count: int

    def setup(self):
        self.count = 0

    @lg.subscriber(INPUT)
    async def run(self, message: InputOutputReturnMessage):
        self.count += 1
        assert message.sample == input_output_function(self.count)


class InputOutputGraph(lg.Graph):
    GENERATOR: InputOutputGenerator
    FUNCTION: InputOutputFunctionNode
    CONSUMER: InputOutputConsumer

    def connections(self) -> lg.Connections:
        return (
            (self.GENERATOR.OUTPUT, self.FUNCTION.INPUT),
            (self.FUNCTION.OUTPUT, self.CONSUMER.INPUT),
        )

    def process_modules(self) -> Tuple[lg.Module, ...]:
        return (self.GENERATOR, self.FUNCTION, self.CONSUMER)


def test_input_output_graph() -> None:
    g = InputOutputGraph()
    runner = lg.ParallelRunner(graph=g)
    runner.run()
