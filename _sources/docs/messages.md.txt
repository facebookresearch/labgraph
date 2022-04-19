# Messages

LabGraph Messages are how we define data types for use in our computational graphs. They work like [dataclasses](https://docs.python.org/3/library/dataclasses.html) in Python (and in fact use dataclasses under the hood), but they have some additional features:

* **Shared memory:** Every message is allocated in shared memory (via Cthulhu, the underlying transport framework for LabGraph). So, we can put large amounts of data into a message and expect that data not to be copied between when we publish it from a node and when we receive it in another node.
* **Fixed vs. dynamic fields:** Some field types, like `int` and `float`, have fixed length, meaning they always take up a fixed amount of space in memory. Others, like `str` and `bytes`, have dynamic length, meaning we don't know how much space they'll take in memory until we create the message. In general, fixed-length field types will be more performant than dynamic-length field types because Cthulhu is able to recycle buffers of the same length more efficiently. However, dynamic-length fields can add useful flexibility when we simply don't know the length of our fields until runtime. We have a default mapping from common types to fixed and dynamic field types, but it is also possible to explicitly create fixed-length fields for `str`, `bytes`, and `numpy.ndarray`.
* **Message type connectability:** Sometimes we want to use different message types for different topics, but still be able to connect them. For example, we may want a field type to be dynamic in general, but fixed when dealing with a particular hardware system. As a result, we allow connecting topics with different message types so long as those types are *connectable*. Two message types are connectable if:
   1. They have the same number of fields, and
   2. For every *i*, the *i*th field in each message type is connectable, where two fields are connectable if:
      1. They are both fixed-length fields with the same length, or
      2. They are both dynamic-length fields, or
      3. They are a fixed-length field and a dynamic-length field with the same underlying Python type

Here is a simple example of connectability:

```python
class MyMessage1(df.Message):
  field1: int
  field2: df.NumpyType(shape=(100, 100))

class MyMessage2(df.Message):
  field1: df.BytesType(length=8)
  field2: np.ndarray

class MyMessage3(df.Message):
  field1: int
  field2: df.NumpyType(shape=(100, 200))
```
Here are the connectability statements we can make:

* **MyMessage1 and MyMessage2 are connectable.** The field1 fields are fixed-length fields of the same length (8 bytes), and the field2 fields are a fixed and dynamic field with the same underlying Python type (`np.ndarray`).
* **MyMessage2 and MyMessage3 are connectable.** This is very similar to the previous statement. The field1 fields are fixed with the same length, and the field2 fields are fixed and dynamic, but both `np.ndarray`.
* **MyMessage1 and MyMessage3 are not connectable.** This is because while their field1 fields are connectable, their field2 fields are fixed-length fields with different lengths, so they are not connectable.

The implication of this is that a stream cannot have two topics with types `MyMessage1` and `MyMessage3`. The other pairings would be fine, though.
