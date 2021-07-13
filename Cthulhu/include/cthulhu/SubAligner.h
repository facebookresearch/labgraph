// Copyright 2004-present Facebook. All Rights Reserved.

#pragma once

#include <cthulhu/Aligner.h>

#include <set>
#include <unordered_map>
#include <variant>

namespace cthulhu {

namespace subaligner {
class Aligner;
struct StreamInterface;
struct Manifest;
} // namespace subaligner

class SubAligner : public AlignerBase {
 public:
  struct StreamSettings {
    // Offset the input stream by this value (in seconds)
    double timeOffset = 0.0;
    // Flag for whether to install a metronome for the stream, default true
    bool useMetronome = true;
  };

  SubAligner(
      const std::vector<StreamSettings>& settings = std::vector<StreamSettings>(),
      const ThreadPolicy& threadPolicy = ThreadPolicy::SINGLE_THREADED);
  virtual ~SubAligner();

  // By default, all streams will use metronomes unless settings have been set.
  // Use this to change that default
  void setDefaultMetronome(bool value);

  // This will apply a specific stream setting based on the StreamID, if used. This
  // will override any settings that are based on the pin ordering
  void setStreamSettingHint(const StreamID& id, const StreamSettings& settings);

  // Select primary stream (e.g. stream that is choosing the alignment time spans)
  //
  // Must be called after all streams have been registered. May be changed during alignment.
  void setPrimaryAlignmentStream(const StreamID& id, double maxLatencySeconds);

  virtual void registerConsumer(StreamInterface* si, int index) override;

  // Returns the largest latency offset specified across all stream settings
  double getMaxLatencyOffset() const;
  // Returns true if the stream ID is a registered stream
  bool isRegistered(const StreamID&) const;

 protected:
  // Note: The currently implementation of align() is not thread-safe with
  // itself, multiple concurrent calls will run into trouble if we ever try to support
  // a MULTI_THREADED mode for the aligner.
  virtual void align() override;
  virtual void sampleCallback(size_t idx, const StreamSample& sample) override;
  virtual bool configCallback(size_t idx, const StreamConfig& config) override;
  virtual void clear() override;

  // This is data stored for a stream, which is coupled to a specific aligner context
  struct ContextStreamData {
    // The config data for the stream within this context
    StreamConfig config;
    // Samples, indexed in the sequence domain of the context (starting with sequenceIn for each
    // sample fed to the context)
    std::unordered_map<uint32_t, StreamSample> sampleMap;
    // Lock for the sampleMap and interface (feed)
    std::mutex streamMutex;
    // The interface to the SubAlignerImpl for this stream
    subaligner::StreamInterface* interface;
    // The next sample sequence number for the stream in this context.
    uint32_t sequenceIn = 0;
  };

  // A sample finalization strategy that relies on user-selection of a primary stream
  //
  // When this is the finalization strategy, we will finalize samples that have timestamps
  // outside of the primary stream's latest sample + a maximum latency. Moreover, we will
  // outright reject samples that are older than the primary stream's latest sample, plus
  // latency.
  //
  // Example:
  //    Suppose the primary stream's latest timestamp is 3.14. Our maximum latency is 0.5.
  //    We will finalize and reject the samples of all streams that are older than
  //    3.14 - 0.5 = 2.64 seconds.
  class PrimarySelection {
   public:
    PrimarySelection(StreamID streamID, int index, double maxLatencySeconds)
        : maxLatencySeconds(maxLatencySeconds), streamID_(std::move(streamID)), index_(index) {}

    // Returns the index of the primary stream selection
    int getIndex() const noexcept {
      return index_;
    }

    inline const StreamID& getStreamID() const noexcept {
      return streamID_;
    }

    // Sets the reference timestamp to be used with isWithinTolerance
    inline void setReference(double referenceTimestamp) noexcept {
      referenceTimestamp_ = referenceTimestamp - maxLatencySeconds;
    }

    // Returns true if the supplied timestamp is within the time of tolerance
    // for new samples.
    inline bool isWithinTolerance(double timestamp) const noexcept {
      return timestamp >= referenceTimestamp_;
    }

    // A relative time (seconds) that describes how much latency we'll
    // tolerate
    double maxLatencySeconds;

   private:
    // Primary stream ID
    StreamID streamID_;
    // Index of the primary stream
    int index_;
    // The timestamp we use as our reference for what's considered too
    // old to align. Accounts for the max latency.
    double referenceTimestamp_;
  };
  // A simpler finalization strategy that relies on a global, maximum latency (seconds).
  //
  // When a sample arrives with timestamp T, we tell the aligner to finalize any data that arrives
  // before T - GlobalMaxLatency.
  using GlobalMaxLatency = double;
  // The finalization strategy.
  std::variant<GlobalMaxLatency, PrimarySelection> finalizeStrategy_ = GlobalMaxLatency(0.5);

  // A new aligner must be constructed for each new configuration
  struct AlignerContext {
    // The pointer to the Implementation for the context
    std::unique_ptr<subaligner::Aligner> impl;
    // References to context-specific data for each stream. Indexed by the same ordering as in
    // SubAligner::streams_
    std::map<int, ContextStreamData> streams;
    // Lock for the impl (enroll, align, finalize) and streams
    std::mutex implMutex;
    // Reverse lookup from Impl's idx to ours (this is probably always trivial out == in
    std::map<int, int> lookupIndex;
    // Flag for whether the context has been configured. Can only be configured once.
    bool configured = false;
  };

  // The SubAlignerImpl is built with the underlying assumption that sample rates, etc. do not
  // change. But Cthulhu allows streams to be dynamically reconfigured. This is supported by
  // creating new contexts in which the SubAlignerImpl is accessed, such that newly configured
  // streams start using a new instance.
  std::map<int, AlignerContext> contexts_;

  // You should lock this when modifying the contexts_ and streams_
  std::mutex globalMutex_;

  struct GlobalStreamData {
    // The unique ID for the stream
    StreamID streamID;
    // The consumer on which samples and configuration should be sent
    std::unique_ptr<StreamConsumer> consumer;
    // The context actively being used by this stream
    int activeContext = -1;
    // The next sequence number to apply to output samples
    uint32_t sequenceOut = 0;
  };

  // This is data for each input stream that is useful regardless of the impl context that is active
  std::vector<GlobalStreamData> streams_;

  void enroll(
      size_t idx,
      const StreamConfig& config,
      AlignerContext& context,
      const std::lock_guard<std::mutex>& globalMutexLock);

  void processManifests(
      const std::vector<subaligner::Manifest>& manifests,
      const std::lock_guard<std::mutex>& globalMutexLock,
      AlignerContext& context);

  // This holds the index to the most recently created context
  // Samples received on streams will automatically update to using this latest context.
  int latestContext_ = -1;

  // Latency in seconds at which old records are cleared from the queues
  // This is a nominal value, but if the primary stream has a nominal sample
  // rate, this will automatically adjust to 0.5*sampleRate_primary + max(timeOffsets)
  static constexpr double maxLatencyFraction_ = 2.5;

  // Settings for each stream (optional)
  std::vector<StreamSettings> settings_;

  // Hints for settings that override any others based on the stream ID
  std::map<StreamID, StreamSettings> settingHints_;

  bool defaultUseMetronome_ = false;

}; // class AlignerBase

// Implements various primary alignment stream selection approaches
class PrimaryAlignmentStream {
 public:
  struct Election {
    StreamID streamID;
    double maxLatencySeconds = 0.0;
  };

  // Elects the best image stream to be the primary alignment stream
  //
  // streamIDs may describe a stream of any type; the implementation will filter
  // the streamIDs to those that describe image streams. Then, the implementation looks at
  // all published image configurations. It selects one of the slowest streams, and defines
  // a maximum latency (seconds) based on the frame rate.
  //
  // If there is no election, returns an empty optional. If the user specifies a streamID that
  // is unknown to the aligner, throws a runtime exception, since we could not run a valid election.
  static std::optional<Election> bestImageStream(
      const SubAligner&,
      const std::vector<StreamID>& streamIDs,
      double maxLatencyFraction = 2.5);
};

} // namespace cthulhu
