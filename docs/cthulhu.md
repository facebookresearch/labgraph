# Cthulhu

Cthulhu is a flexible real-time streaming and synchronization framework.

## What is Cthulhu?

Cthulhu is a C++ library with minimal software dependencies. It provides an API for building low-latency processing graphs using standardized and customizable stream types.

So, it's a pub/sub framework, why not just use <other framework>?
 1. Cthulhu's API enables explicit construction of a graphical flow of data. Think of pub/sub as the single-input or single-output cases, whereas Cthulhu enables multi-input-multi-output (MIMO) compute tasks. This enables the framework to automatically track the flow of individual samples through the pipeline, and produce end-to-end historical latency tracking of any sample. In the future, it may also provide a convenient API for dynamic flow control within the graph.
 2. Typical pub/sub frameworks focus on distributed socket-based communication. For systems with light-weight metadata streams, this works just fine. But with perception systems, we often use high-bandwidth data on our stream interfaces. Cthulhu allocates and recycles data buffers from shared memory, and exposes them to the user as ordinary shared pointer to enable transparent low-latency IPC to consumers that live in other processes on the same machine.

Cthulhu is currently supported on Windows, Mac, Linux, and Android.

## Why should I care?

Cthulhu enables tooling and infrastructure reuse across real-time pipelines, and modularity for reuse of subcomponents. For a user that builds a new pipeline using entirely existing stream types and compute functions, all tooling comes for free.

## Streams

To use Cthulhu, first you must define the layout of your streaming data. Cthulhu comes packaged with a few fundamental types such as image and audio streams, but provides an API for users to register their own types without modification to the Cthulhu library.

A sample of a stream has 4 components:
 - Header - Unique identifying information.
   - Timestamp
   - Sequence
 - ProcessingTimestamp(s) [Optional] - It is possible to tag a sample with timestamps that are associated with stages in the processing chain at which it was developed. An example would be the time at which an image was received in user-space software from a camera device.
 - Content Block [Optional] - This is variable size bulk data. Think of it as the pixel data in an image. The size of the block must be derivable from the Config Fields (more on that later). This block can also be broken out into a set of sub-samples that is specified by an additional field. By default, the block is composed of a single sub-sample.
 - Sample Field(s) [Optional] - These are light-weight fixed-size fields. Each field is named, and must be POD.

A user can define a sample format by inheriting from cthulhu::AutoStreamSample:

```c++
class ImageData : public AutoStreamSample {
  using T = ImageData;

 public:
  // We are free to name each parameter as desired
  HeaderTimestamp captureTimestamp{this};
  HeaderSequence frameNumber{this};

  // Define the name which the processing stamp will be given
  ProcessingTimestamp arrivalTimestamp{"arrival", this};

  // If we want a Content Block, just add one with any parameter name.
  ContentBlock<T> data{this};

  // All fields must be sandwiched between a FieldsBegin and FieldsEnd
  FieldsBegin<T> begin;
  // Define the type (here uint32_t),
  SampleField<uint32_t, T> strideInBytes{"image_stride", this};
  SampleField<uint32_t, T> offsetInBytes{"offset", this};
  FieldsEnd<T> end;

  // This must be called as public, and takes the class name as argument
  CTHULHU_AUTOSTREAM_SAMPLE(ImageData);
};
```

If a stream has no Content Block, it is called a "Basic Stream." And your journey ends here. Put this in a header, and call the basic registration function from the corresponding cpp source file:

```c++
CTHULHU_REGISTER_BASIC_STREAM_TYPE(Image, cthulhu::ImageData);
```

This registers the type to the identified "Image", which must be unique across all actively communicating Cthulhu runtimes.

If your stream includes a Content Block, it must also provide a Configuration which can be used to configure the Stream's Content Block format. This is similar to the Sample definition, but has the following components:

 - Compute Sample Size Function - This function must return the size of the Content Block being actively streamed. If the block is broken into sub-samples, it is the size of a single sub-sample.
 - Sample Rate [Optional] - This is the nominal rate of samples being streamed.
 - Config Field(s) - Similar to Sample Fields, but at least one field is required for use in the Compute Sample Size Function.

Here is an example:

```c++
enum class PixelFormat : uint32_t { INVALID = 0, MONO_8 = 1, MONO_10 = 2, YUY2 = 3, COUNT };

class ImageFormat : public AutoStreamConfig {
  using T = ImageFormat;

 public:
  SampleRate nominalSampleRate{this};

  FieldsBegin<T> begin;
  ConfigField<uint32_t, T> width{"image_width", this};
  ConfigField<uint32_t, T> height{"image_height", this};
  ConfigField<PixelFormat, T> pixelFormat{"pixel_format", this};
  FieldsEnd<T> end;

 // This is the pure-virtual function that must be overridden
  inline virtual uint32_t computeSampleSize() const override {
    switch (pixelFormat) {
      case PixelFormat::MONO_8:
        return width * height;
      case PixelFormat::MONO_10:
        return (width * height * 10) / 8;
      case PixelFormat::YUY2:
        return 2U * width * height;
      default:
        return 0;
    };
  };

  CTHULHU_AUTOSTREAM_CONFIG(ImageFormat);
};
```

This stream can then be registered as an ordinary stream type:
```c++
CTHULHU_REGISTER_STREAM_TYPE(Image, cthulhu::ImageData, cthulhu::ImageFormat);
```

If a stream type is registered in a static library, it is important to ensure that symbols required for type registration get linked into the final executable. Using BUCK, these libraries should set `link_whole = True`.

To work with the components of the streams, such as ConfigFields, they come with set()/get() functions, and also overload operator=() for convenience. So you can access them just like you would an ordinary data field. Underneath the hood, these types are just thin wrappers over a single generic StreamSample data structure object. This enables the framework to cast between typed and untyped data with minimal overhead, while providing regularized structure to the untyped data that allows it to work its magic without embedding the data in an additional container.

You may ask: but what if I need multiple content blocks in my stream? The answer is, you don't. If you need an additional content block, then you need an additional stream. Cthulhu's APIs make it just as easy and performant to work with multiple streams instead of just one, so your system will thank you for the modularity of splitting out the data.

## Nodes

Nodes are a logical unit of compute within the pipeline which receives N data streams in to produce M data streams out. Cthulhu provides an API for convenient construction of Nodes.

Here's an example of the most basic pub/sub behavior using a "Basic" stream type with sample type BasicSample:

```c++
cthulhu::Context myContext("my_context");

std::function<void(const BasicSample&)> cb =
      [](const BasicSample& sample) -> void {};
auto subscriber = myContext.subscribe("stream_name", cb);

auto publisher = myContext.advertise<BasicSampleType>("stream_name");
BasicSampleType mySample;
publish.publish(mySample);
```

Since both the producer and the consumer in this example are in the same process, underneath the hood the call to publish() is directly calling the callback "cb" without any queueing or additional threads. This is great for cases where consumers are super-light-weight processing that have minimal penalty in injecting their function directly in the producer's thread since the data will reach the consumer with the least latency.

But what if we had a heavy consuming function that needed its own thread or would otherwise slow down the consumer? That's what SubscriberOptions are for. We can call subscribe() with an additional options parameter which sets the ConsumerType to ASYNC. This will cause the subscriber to dedicate its own thread for processing its callback function. In this case, the publish() call will now push mySample to an async queue and notify the subscriber's thread.

For usage of only single input or single output Nodes and basic stream types, this API looks a lot like basic pub/sub. Next, let's explore how we use an ordinary stream that uses both Config and Samples:

```c++
// Subscribers must now specify two callbacks, one for sample and one for config
// The config callback returns bool. With
std::function<void(const cthulhu::ImageData&)> cb =
    [](const cthulhu::ImageData& image) -> void { callback_executed = true; };
std::function<bool(const cthulhu::ImageFormat&)> configCb =
    [](const cthulhu::ImageFormat& format) -> bool {
  return true;
};

auto sub = context.subscribe("image", cb, configCb);

auto pub = context.advertise<cthulhu::ImageData>("image");

// We must configure our stream before we publish any samples on it!
// The config must produce a valid return value of computeSampleSize(), so here we set
// the height and width of the image to something valid
cthulhu::ImageFormat format;
format.width = 640;
format.height = 480;
format.pixelFormat = cthulhu::PixelFormat::MONO_8;
pub->configure(format);

// We must use our publisher to allocate our sample data!
// This will leverage the current config of the stream, which is a 640 x 480 image
cthulhu::ImageData image = pub->allocateSample<cthulhu::ImageData>();
pub->publish(image);
```

The difference here is that we now have 2 callbacks, and must call configure() before any calls to publish() on the stream. The Sample must also be allocated using the publisher since it has a Content Block.

Calls to publish() and configure() are not thread safe. Thus, you should only push data to a producing Node on a single thread. Conversely, the config and sample callbacks do not need to handle thread safety. The user can assume that the two types of callbacks will only come from a single thread.

So far, we've only explored single input and single output Nodes. Next, let's look at a Transformer with both an input and an output:

```c++
std::function<void(const cthulhu::ImageData&, cthulhu::ImageData&)> cb =
    [](const cthulhu::ImageData& image, cthulhu::ImageData& imageOut) -> void {};
std::function<bool(const cthulhu::ImageFormat&, cthulhu::ImageFormat&)> configCb =
    [](const cthulhu::ImageFormat& format, cthulhu::ImageFormat& formatOut) -> bool {
  formatOut.width = 640;
  formatOut.height = 480;
  formatOut.pixelFormat = cthulhu::PixelFormat::MONO_8;
  return true;
};

auto trans =
    context.transform<cthulhu::ImageData, cthulhu::ImageData>("image1", "image2", cb, config_cb);
```

This should look like a mix between the Publisher and Subscriber, because it is. The main difference is that the user is not responsible for allocating its output samples, as the framework will provide it to the callback pre-allocated. Configuring the output stream also happens within the callback to the configuration of the input stream. In many cases, the two configurations may be un-related, but this gives the flexibility in allowing the user to tie the two together. For example, an RGB to Grayscale transformer would maintain the height/width of the original image and expect the input pixel format to be RGB.

Similar to Subscriber, this can be given TransformerOptions optionally to specify ASYNC mode.

Finally, the most complex case of multi-input, multi-output, here is an example:

```c++
std::function<void(const std::vector<cthulhu::ImageData>&, std::vector<cthulhu::ImageData>&)> cb =
    [](
        const std::vector<cthulhu::ImageData>& imagesIn,
        std::vector<cthulhu::ImageData>& imagesOut) -> void {};
std::function<bool(const std::vector<cthulhu::ImageFormat>&, std::vector<cthulhu::ImageFormat>&)>
    configCb = [](const std::vector<cthulhu::ImageFormat>& imagesIn,
                  std::vector<cthulhu::ImageFormat>& imagesOut) -> bool { return true; };
cthulhu::MultiTransformer trans = context.transform(
    {std::vector<cthulhu::StreamID>{"image1", "image2"}},
    {std::vector<cthulhu::StreamID>{"image3"}},
    cb,
    configCb);
```

This should look just like the regular transformer, but now the input stream and output streams are lists of stream ID's rather than single values. The callback arguments can also be grouped together with std::vector or std::array, which can be handy for cases where you have a large number of input or output streams of the same type.

Underneath the hood, Cthulhu is creating Producers and Consumers for each of these streams, and joining them together in an Aligner and a Dispatcher. The default Alignment behavior is based on timestamp matching with a max latency and tolerance threshold. The user can create their own variants of Aligner and pass them via MultiTransformerOptions (or MultiSubscriberOptions). This allows for customizable alignment behavior. Cthulhu comes packaged with an additional SubAligner implementation that can align the sub-samples of streams within a Content Block. This requires any stream using sub-samples to include a Sample Rate within its Config.

## Clock

Cthulhu also provides a clock interface, useful for system simulation. A user should query time through cthulhu:
```c++
auto time = cthulhu::clock()->getTime();
```
By default, this will just return wall time. However, a single context name can be given clock authority to control time. This should be whichever context is being used to control the flow of data via Publishers.
```c++
int main() {
  // Declare use of simulated time, with clock_owner as the context
  cthulhu::ClockAuthority fac(true, "clock_owner");

  ...

  // This context can now control time
  cthulhu::Context owningContext("clock_owner");
  owningContext.getClockControl()->setTime(500.0);
  owningContext.getClockControl()->start();

  // And this one cannot
  cthulhu::Context otherContext("some_context");
  otherContext.getClockControl(); // Returns nullptr
}
```

Listeners of the clock can subscribe to events, such as start, pause, etc.

## Framework

All of the above is sufficient for most users of Cthulhu to accomplish their goal. However, these functionalities under the hood are using the Cthulhu Framework Singleton to achieve their goals. The Framework has 4 components:
 - TypeRegistry - Provides access to information about stream types that have been registered. E.g. names of fields, basic flag, sizes, etc.
 - StreamRegistry - Provides access to stream interfaces on which data can be propagated (using raw StreamConfig and StreamSample's)
 - MemoryPool - Allocates recyclable data buffers (from local memory, shared memory, etc)
 - ClockManager - Manages the state of the clock, and access to its controls

Currently, the default implementation of Framework is called "IPCHybrid." This implementation uses a mix of managed shared memory and local memory to achieve its goals with minimal latency. Thus, interactions between nodes in the same process don't have to go through shared memory and callbacks are executed directly. The CTHULHU_IPC compiler flag will set this, and removal of the flag will compile against a "Local" implementation of Framework that is restricted to a single process.
