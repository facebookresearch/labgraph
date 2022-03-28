# Copyright 2004-present Facebook. All Rights Reserved.

import asyncio
import inspect
from dataclasses import asdict, astuple, dataclass, field
from functools import wraps
from hashlib import sha1
from inspect import Parameter, signature
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

import labgraph as lg
from toolz import curry
from ..utils.doc.docfill import fill_in_docstring


# The documentation for this function is very long; to make the function itself
# easier to read, the documention is moved here.
_argument_doc = fill_in_docstring(
    {
        "f": """f: Callable[[Any], Any]
          The function to convert to a node.
      """,
        "base_cls": """base_cls: lg.Message = lg.Message
        The class to inherit from for the ArgumentMessage and ReturnMessage.
        All parameters inherited from this base class are passed through
        directly to the output topic of the function node without alteration.
      """,
        "keyword_only_in_message": """keyword_only_in_message: bool = False,
        Whether to include keyword only arguments in the message type. If
        false, keyword only arguments can be passed only through the
        `FunctionConfig` object; if true, the keyword arguments become fields
        in the ArgumentMessage type.
      """,
        "default_keyword_in_message": """default_keyword_in_message: bool = False,
        Whether to include arguments that have a default value in the
        ArgumentMessage type.
      """,
        "deconstruct_dataclass_return_type": """deconstruct_dataclass_return_type: bool = True,
        If a function returns a dataclass, setting this to true will make the
        fields of the dataclass fields in the ReturnMessage class.
      """,
        "single_return_param_name": """single_return_param_name: str = "sample",
        What to name the output message field parameter. If
        `deconstruct_dataclass_return_type` is set to True, this parameter has
        no effect.
      """,
        "argument_topic_name": """argument_topic_name: str = "INPUT",
        Name of the input/argument topic in the FunctionNode.
      """,
        "return_topic_name": """return_topic_name: str = "OUTPUT",
        Name of the output/return topic in the FunctionNode.
      """,
        "sleep_time": """sleep_time: float = 0.01,
        If the function is a source (has no argument), how long should the
        process wait before running the function again.
      """,
        "error": """error: Callable[[str], None] = lambda x: None,
        The function to use to collect errors with. Multiple errors can be
        captured during a function call.
      """,
    }
)

###############################################################################
#                                    Types                                    #
###############################################################################


@dataclass
class FunctionToNode:
    ArgumentMessage: Optional[lg.Message]
    ReturnMessage: Optional[lg.Message]
    FunctionNode: lg.Node

    def __iter__(self):
        return iter(astuple(self))


class FunctionConfig(lg.Config):
    kwargs: Dict[str, Any] = field(default_factory=dict)


class _BlankMesage(lg.Message):
    pass


###############################################################################
#              Helper functions to determine function parameters              #
###############################################################################


def is_keyword(arg):
    return (
        arg.kind is Parameter.POSITIONAL_OR_KEYWORD
        or arg.kind is Parameter.KEYWORD_ONLY
    )


def is_keyword_only(arg):
    return arg.kind is Parameter.KEYWORD_ONLY


def is_nondefault_keyword(arg):
    return is_keyword(arg) and arg.default is Parameter.empty


def is_default_keyword(arg):
    return is_keyword(arg) and arg.default is not Parameter.empty


def positionally_passed(arg):
    return (arg.kind is Parameter.POSITIONAL_ONLY) or (
        arg.kind is Parameter.POSITIONAL_OR_KEYWORD and arg.default is Parameter.empty
    )


def call_with_error(error_type):
    """Collects a bunch of errors and returns them all once.

    Decorator that collects the errors in the decorated function so that the
    user can see everything they need to fix at once. All errors are thrown
    with the same error type.

    The decorated must have an `error` keyword parameter. The `error` parameter
    is then ignored if the end user passes in that argument.

    Parameters
    ----------
    error_type: type
        The type of error to throw. For example, `ValueError`.

    Returns
    -------
    Callable[Callable[[Any], Any], Callable[[Any], Any]]
        Returns a decorator

    Example
    -------
    >>> @call_with_error(ValueError)
    >>> def func(a: int, b: int, error: Callable[[str], None]) -> int:
    ...     if a < 0:
    ...         error("a must be zero or greater")
    ...     if b < 0:
    ...         error("b must be zero or greater")
    ...     return a + b

    >>> func(-1, 0)
    ValueError("a must be zero or greater")

    >>> func(0, -1)
    ValueError("b must be zero or greater")

    >>> func(-1, -1)
    ValueError("a must be zero or greater\nb must be zero or greater")
    """

    def _call_with_error(f):
        @curry
        def error(log, msg):
            log.append(msg)

        @wraps(f)
        def wrapped(*args, **kwargs):
            log = []
            result = f(*args, error=error(log), **kwargs)
            if len(log) > 0:
                raise error_type("\n".join(log))
            return result

        return wrapped

    return _call_with_error


###############################################################################
#                 Determine function argument and return types                #
###############################################################################


@_argument_doc
def parse_argument_annotations(
    argument_annotations: Tuple[Parameter, ...],
    function_name: str,
    keyword_only_in_message: bool,
    default_keyword_in_message: bool,
    error: Callable[[str], None],
) -> Optional[Dict[str, type]]:
    """Parse which argument_annotations should be placed into a Labgraph Message.

    The primary purpose of this function is to collect which parameters should
    be passed to the final lg.Node through a lg.Message and which should be
    passed through either default values or FunctionConfig.

    Parameters
    ----------
    argument_annotations: Tuple[Parameter, ...]
        The argument_annotations to a function, as Parameter objects.
    function_name: str
        The name of the function the argument_annotations came from.
    {keyword_only_in_message}
    {default_keyword_in_message}
    {error}

    Returns
    -------
    Optional[Dict[str, type]]
        If no argument_annotations are provided, then None is returned. Else a
        dictionary of argument names and types that are to go into a Labgraph
        Message is returned.
    """
    # Error handling components
    var_err_msg = (
        f"Function `{function_name}` takes in a variable {{var_type}} parameter "
        f"named `{{arg_name}}`. Functions with variable {{var_type}} parameters "
        f"cannot be converted to Labgraph nodes using `function_to_node`."
    )

    # Functions with no argument_annotations are sources of data (type `() -> A`).
    if len(argument_annotations) == 0:
        return None

    argument_types = {}
    for arg in argument_annotations:
        # We do not support variable argument_annotations since we can't determine how
        # many fields to make in the return Labgraph message.
        if arg.kind is Parameter.VAR_POSITIONAL:
            error(var_err_msg.format(var_type="argument", arg_name=arg.name))

        if arg.kind is Parameter.VAR_KEYWORD:
            error(var_err_msg.format(var_type="keyword argument", arg_name=arg.name))

        if arg.annotation is Parameter.empty:
            error(
                f"Function `{function_name}` argument with name `{arg.name}` does not "
                f"have a type annotation. All parameters require a type annotation to "
                f"convert the function to a Labgraph node using `function_to_node`."
            )

        if positionally_passed(arg):
            argument_types[arg.name] = arg.annotation

        elif default_keyword_in_message and is_default_keyword(arg):
            # Python prevents us from having functions where one parameter is
            # POSITIONAL_OR_KEYWORD with a default and another parameter that
            # is KEYWORD_ONLY without a default. This means we can assume that
            # default keyword arguments must be after non-default arguments.
            # i.e the following is illegal.
            #   def f(a, b: bool = True, *, c:str)
            argument_types[arg.name] = arg.annotation

        elif keyword_only_in_message and is_keyword_only(arg):
            # We could potentially want default keywords to not be in the final
            # message type and pass those in by default or through the
            # `FunctionConfig` `kwargs` parameter.
            if not default_keyword_in_message and is_default_keyword(arg):
                pass
            else:
                argument_types[arg.name] = arg.annotation

    return argument_types


@_argument_doc
def parse_return_annotation(
    return_annotation: type,
    deconstruct_dataclass_return_type: bool,
    single_return_param_name: str,
) -> Tuple[Optional[Dict[str, type]], bool]:
    """Parse return annotation into something Labgraph can use.

    This function is primarily for unpacking return types that have an
    __annotations__ property. We use this property to move the contents of the
    return type directly into the final return lg.Message fields for
    convenience and efficiency.

    Parameters
    ----------
    return_annotation: type
        The return type of a function
    {deconstruct_dataclass_return_type}
    {single_return_param_name}

    Returns
    -------
    Tuple[Optional[Dict[str, type]], bool]
        If no return type is provided, then (None, False) is returned. Else a
        dictionary of the potentially deconstructed return names and types that
        are to go into a Labgraph Message is returned, along with a bool of
        whether the deconstruction occurred.
    """
    # Base case of a sink function.
    return_types = None
    unpack_return = False

    # We have a function that is something besides a sink.
    if return_annotation is not Parameter.empty:

        # We have a sink function (a function that returns nothing)
        if return_annotation is None:
            return_types = None
            unpack_return = False

        # If the return type has an __annotations__ field we can attempt to
        # unpack the results into the message directly.
        elif deconstruct_dataclass_return_type and hasattr(
            return_annotation, "__annotations__"
        ):
            return_types = {
                name: typ for name, typ in return_annotation.__annotations__.items()
            }
            unpack_return = True

        # If the return type is anything else, do nothing with it but store it
        # in the specified name.
        else:
            return_types = {single_return_param_name: return_annotation}
            unpack_return = False

    return return_types, unpack_return


@call_with_error(ValueError)
def parse_function_annotations(
    f: Callable[..., Any],
    keyword_only_in_message: bool = False,
    default_keyword_in_message: bool = False,
    deconstruct_dataclass_return_type: bool = True,
    single_return_param_name: str = "sample",
    error: Callable[[str], None] = lambda x: None,
) -> Tuple[Optional[Dict[str, type]], Optional[Dict[str, type]], bool]:
    """Convert function annotations into the fields to be turned into the
    Labgraph Message argument and return types.

    Parameters
    ----------
    {f}
    {keyword_only_in_message}
    {default_keyword_in_message}
    {deconstruct_dataclass_return_type}
    {single_return_param_name}
    {error}

    Returns
    -------
    Tuple[Optional[Dict[str, type]], Optional[Dict[str, type]], bool]
        Dictionaries containing the argument types (if they exist), the return
        types (if they exist), and a flag on if the return type was
        deconstructed into its constituent pieces.
    """

    sig = signature(f)
    name = f.__name__

    argument_annotations = tuple(p for _, p in sig.parameters.items())
    return_annotation = sig.return_annotation

    # Returned parameters. Setting them all to the base case of no result.
    argument_types = parse_argument_annotations(
        argument_annotations,
        name,
        keyword_only_in_message,
        default_keyword_in_message,
        error,
    )
    return_types, unpack_return = parse_return_annotation(
        return_annotation, deconstruct_dataclass_return_type, single_return_param_name
    )

    if argument_types is None and return_types is None:
        error(
            f"Function `{name}` does not take or return any values. The function must "
            f"either take a value, return a value, or take and return a value to be "
            f"converted to a Labgraph node."
        )

    return (argument_types, return_types, unpack_return)


###############################################################################
#                  Message to dict (and reverse) conversions                  #
###############################################################################


def extract_message_fields(message: lg.Message, fields: List[str]) -> Dict[str, Any]:
    return {field: getattr(message, field) for field in fields}


def remove_dict_keys(d: Dict[str, Any], fields: Set[str]) -> Dict[str, Any]:
    return {name: value for name, value in d.items() if name not in fields}


def generate_message_class(
    function_name: str,
    message_class_name: str,
    types: Optional[Dict[str, type]],
    base_cls: type,
) -> type:

    # We do not generate a Message class when there are no types associated
    # with either the arguments or return of a function.
    if types is None:
        return None

    # The `hash` function is not stable; it can return different results
    # for the same input in different processes or on different platforms.
    type_hash = sha1(repr(types.items()).encode("ascii")).hexdigest()

    # We put the hash in the message class name in order to prevent name
    # clashes in cthulhu.
    return type(
        f"{message_class_name}_{function_name}_{type_hash}",
        (base_cls,),
        {"__annotations__": dict(types)},
    )


###############################################################################
#                        Convert functions into classes                       #
###############################################################################


class _BlankMessage(lg.Message):
    """This class is for passing someting to `call` in the source case. It
    removes some branching logic that would reduce the readability of the
    `call` function."""

    pass


@_argument_doc
def function_to_node(
    f: Callable[[Any], Any],
    base_cls: lg.Message = lg.Message,
    keyword_only_in_message: bool = False,
    default_keyword_in_message: bool = False,
    deconstruct_dataclass_return_type: bool = True,
    single_return_param_name: str = "sample",
    argument_topic_name: str = "INPUT",
    return_topic_name: str = "OUTPUT",
    sleep_time: float = 0.01,
) -> FunctionToNode:
    """Convert a function to a labgraph node that operates on every message.

    For example, to lifting the following function:

    ```
    def f(a: int, b: int = 2) -> int:
        return a * b * 4

    ArgumentMessage, ReturnMessage, FunctionNode = function_to_node(f)

    # or
    function_node = function_to_node(f)
    ArgumentMessage = function_node.ArgumentMessage
    ReturnMessage = function_node.ReturnMessage
    FunctionNode = function_node.FunctionNode
    ```

    is the same as the following code

    ```
    def f(a: int, b: int = 2) -> int:
        return a * b * 4

    class ArgumentMessage(lg.Message):
        sample: int

    class ReturnMessage(lg.Message):
        sample: int

    class FunctionNode(lg.Node):
        INPUT = lg.Topic(ArgumentMessage)
        OUTPUT = lg.Topic(ReturnMessage)

        # keyword parameters can be passed by this config object, which takes a
        # "kwargs" field with a dictionary value.
        config: FunctionConfig

        @lg.subscriber(INPUT)
        @lg.publisher(OUTPUT)
        async def run(self, message: ArgumentMessage) -> lg.AsyncPublisher:
            to_value = f(message.sample, **self.config.kwargs)
            yield self.OUTPUT, ReturnMessage(sample=to_value)
    ```

    Note that if you would like to use the node in its own process (through the
    `process_modules` method in a class), you MUST assign the results of this
    function to the module namespace. This allows the returned classes to be
    called from each process.

    Parameters
    ----------
    {f}
    {base_cls}
    {keyword_only_in_message}
    {default_keyword_in_message}
    {deconstruct_dataclass_return_type}
    {single_return_param_name}
    {argument_topic_name}
    {return_topic_name}
    {sleep_time}

    Returns
    -------
    FunctionToNode
        Returns a type for the input Message, output Message, configuration
        (keyword arguments) and Node that runs the function.
    """
    function_name = f.__name__

    argument_types, return_types, unpack_return = parse_function_annotations(
        f,
        keyword_only_in_message=keyword_only_in_message,
        default_keyword_in_message=default_keyword_in_message,
        deconstruct_dataclass_return_type=deconstruct_dataclass_return_type,
        single_return_param_name=single_return_param_name,
    )

    # Generate message classes and topics ############################

    base_cls_fields = base_cls.__message_fields__

    ArgumentMessage = generate_message_class(
        function_name, "ArgumentMessage", argument_types, base_cls
    )
    ReturnMessage = generate_message_class(
        function_name, "ReturnMessage", return_types, base_cls
    )

    topics = {}

    if argument_types is not None:
        argument_topic = lg.Topic(ArgumentMessage)
        topics[argument_topic_name] = argument_topic

    if return_types is not None:
        return_topic = lg.Topic(ReturnMessage)
        topics[return_topic_name] = return_topic

    # Generic method to call the provided function ###################

    def call(message, kwargs):
        # Any fields from the base message class is passed directly through to
        # the output message. For example, if the base class is
        # `lg.TimestampedMessage`, then the field `timestamp` is passed through
        # to the output message directly.
        pass_through_fields = extract_message_fields(message, base_cls_fields)

        # If we have default keyword allowed but not keyword arguments, we run into
        # a case where the order of argument types skips over an argument. This means
        # that positional only arguments are not called correctly. Since we are not
        # using Python 3.8 for a while, we are going to call everything by keyword
        # instead.
        message_fields = remove_dict_keys(message.asdict(), base_cls_fields)
        if len(kwargs) > 0:
            function_result = f(**{**message_fields, **kwargs})
        else:
            function_result = f(**message_fields)

        if unpack_return:
            result_dict = asdict(function_result)
        else:
            result_dict = {single_return_param_name: function_result}

        if ReturnMessage is not None:
            return ReturnMessage(**{**pass_through_fields, **result_dict})

    # Generate node function linked to topics for source, ############
    # sink, and pipe-through function cases               ############

    if argument_types is None and return_types is not None:

        # Case where function takes in nothing and produces some output (a
        # source function).
        @lg.publisher(return_topic)
        async def run(self) -> lg.AsyncPublisher:
            # We need a loop here of some sort, otherwise the node will only
            # run once.
            while True:
                output_msg = call(_BlankMessage(), self.config.kwargs)
                yield getattr(self, return_topic_name), output_msg
                await asyncio.sleep(sleep_time)

    if argument_types is not None and return_types is None:

        # Case where function takes an input and produces no output (a sink
        # function).
        @lg.subscriber(argument_topic)
        async def run(self, message: ArgumentMessage):  # noqa: F811
            call(message, self.config.kwargs)

    if argument_types is not None and return_types is not None:

        # Case where a function both takes an input and produces an output (the
        # pipe-through case)
        @lg.subscriber(argument_topic)
        @lg.publisher(return_topic)
        async def run(  # noqa: F811
            self, message: ArgumentMessage
        ) -> lg.AsyncPublisher:
            output_msg = call(message, self.config.kwargs)
            yield getattr(self, return_topic_name), output_msg

    # Generate node to call function from prior pieces ###############

    # We provide a __module__ name for the case when the function is called in
    # the top-level module namespace. This allows the node generated from this
    # class to be used as a member of `process_modules` method in a graph.
    caller_frame = inspect.stack()[1]
    caller_module_name = inspect.getmodule(caller_frame[0]).__name__

    FunctionNode = type(
        f"FunctionNode_{function_name}",
        (lg.Node,),
        {
            **topics,
            **{
                "__annotations__": {"config": FunctionConfig},
                "__module__": caller_module_name,
                "run": run,
            },
        },
    )

    return FunctionToNode(ArgumentMessage, ReturnMessage, FunctionNode)
