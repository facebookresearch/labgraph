// Copyright 2004-present Facebook. All Rights Reserved.

#include <cthulhu/SubAligner.h>

#include <cthulhu/Framework.h>

#include "SubAlignerImpl.h"

#define DEFAULT_LOG_CHANNEL "Cthulhu"
#include <fmt/format.h>
#include <logging/Log.h>

#include <algorithm>

namespace {
template <typename clock = std::chrono::steady_clock>
inline double NOW() noexcept {
  return std::chrono::duration<double>(clock::now().time_since_epoch()).count();
}
} // namespace

namespace cthulhu {

SubAligner::SubAligner(
    const std::vector<StreamSettings>& settings,
    const ThreadPolicy& threadPolicy)
    : AlignerBase(threadPolicy), settings_(settings) {
  contexts_[0].impl = std::make_unique<subaligner::Aligner>();
  latestContext_ = 0;
  initThread();
}

SubAligner::~SubAligner() {
  killThread();
  streams_.clear();
}

void SubAligner::setPrimaryAlignmentStream(const StreamID& id, double maxLatencySeconds) {
  // Required to be called after stream registration. So, we don't need
  // to hold the lock when evaluating streams_, since it's not going to
  // change size.
  for (size_t idx = 0; idx < streams_.size(); ++idx) {
    if (streams_[idx].streamID == id) {
      const auto globalLock = std::lock_guard(globalMutex_);
      finalizeStrategy_ = PrimarySelection(id, idx, maxLatencySeconds);
      const auto activeContext = streams_[idx].activeContext;
      auto& context = contexts_.at(activeContext);
      const auto alignerLock =
          std::scoped_lock(context.implMutex, context.streams[idx].streamMutex);
      context.streams[idx].interface->primarize();
      return;
    }
  }
  throw std::runtime_error("Desired primary stream '" + id + "' is not registered.");
}

bool SubAligner::isRegistered(const StreamID& streamID) const {
  const auto found =
      std::find_if(streams_.cbegin(), streams_.cend(), [&streamID](const auto& alignedStream) {
        return alignedStream.streamID == streamID;
      });

  return streams_.cend() != found;
}

double SubAligner::getMaxLatencyOffset() const {
  const auto max = std::max_element(
      settings_.cbegin(), settings_.cend(), [](const auto& left, const auto& right) {
        return left.timeOffset < right.timeOffset;
      });
  const auto maxHint = std::max_element(
      settingHints_.cbegin(), settingHints_.cend(), [](const auto& left, const auto& right) {
        return left.second.timeOffset < right.second.timeOffset;
      });
  const double maxOffset = max != settings_.cend() ? max->timeOffset : 0.0;
  const double maxHintOffset = maxHint != settingHints_.cend() ? maxHint->second.timeOffset : 0.0;
  return std::max(maxOffset, maxHintOffset);
}

void SubAligner::registerConsumer(StreamInterface* si, int index) {
  {
    std::lock_guard<std::mutex> lock(globalMutex_);
    if (streams_.size() <= index) {
      streams_.resize(index + 1);
    }
  }
  SampleCallback callback = [this, index](const StreamSample& sample) -> void {
    sampleCallback(index, sample);
  };
  ConfigCallback ccallback = [this, index](const StreamConfig& config) -> bool {
    return configCallback(index, config);
  };
  streams_[index].streamID = si->description().id();
  streams_[index].consumer = std::make_unique<StreamConsumer>(si, callback, ccallback);
}

void SubAligner::setStreamSettingHint(const StreamID& id, const StreamSettings& settings) {
  settingHints_[id] = settings;
}

void SubAligner::setDefaultMetronome(bool value) {
  defaultUseMetronome_ = value;
}

void SubAligner::align() {
  if (!finalized_) {
    return;
  }

  std::lock_guard<std::mutex> lock(globalMutex_);

  std::set<int> activeContexts;
  {
    for (const auto& stream : streams_) {
      activeContexts.insert(stream.activeContext);
    }
  }

  auto context_itr = contexts_.begin();
  while (context_itr != contexts_.end()) {
    // Clear out old contexts
    if (contexts_.size() > 1 && activeContexts.find(context_itr->first) == activeContexts.end()) {
      context_itr->second.impl->flush();
      context_itr = contexts_.erase(context_itr);
      continue;
    }

    // Run alignment
    std::vector<subaligner::Manifest> manifests;
    {
      std::lock_guard<std::mutex> lock2(context_itr->second.implMutex);
      auto res = context_itr->second.impl->align(-1);
      manifests = context_itr->second.impl->retrieve();
      if (res <= 0 && manifests.empty()) {
        ++context_itr;
        continue;
      }
    }
    processManifests(manifests, lock, context_itr->second);
    ++context_itr;
  }
}

void SubAligner::processManifests(
    const std::vector<subaligner::Manifest>& manifests,
    const std::lock_guard<std::mutex>& globalMutexLock,
    AlignerContext& context) {
  // Flatten data and execute callbacks
  for (auto& manifest : manifests) {
    if (manifest.completed_streams.size() != streams_.size()) {
      for (auto& stream : manifest.references) {
        auto sindex = context.lookupIndex.at(stream.first);
        auto sampleSize =
            std::max(context.streams.at(sindex).config.sampleSizeInBytes, uint32_t(1));
        auto& sampleMap = context.streams.at(sindex).sampleMap;
        for (auto& r : stream.second) {
          if (r.nrbytes_offset + r.nrbytes_length ==
              (r.buffer_tagged.nrsamples_total * sampleSize)) {
            sampleMap.erase(r.buffer_tagged.sequence_number);
          }
        }
      }

      // Log which stream(s) was (were) missing, as it helps with troublshooting
      fmt::memory_buffer buffer;
      bool comma = false;
      for (int stream_idx = 0; stream_idx < streams_.size(); ++stream_idx) {
        if (0 == manifest.completed_streams.count(stream_idx)) {
          fmt::format_to(buffer, "{}{}", comma ? "," : "", streams_[stream_idx].streamID);
          comma = true;
        }
      }

      XR_LOGW(
          "Subaligner::processManifests - Finalized an incomplete manifest, missing: {}",
          buffer.data());
      continue;
    }
    // check if we need to bother with creating output samples when nobody consumes them (e.g. only
    // records alignment metadata)
    const bool samplesNeeded = hasSampleCallback() && !inhibitSampleCallback_;

    std::vector<StreamSample> samples(streams_.size());
    AlignerSamplesMeta samplesMeta(streams_.size());
    for (auto& stream : manifest.references) {
      auto sindex = context.lookupIndex.at(stream.first);
      std::lock_guard<std::mutex> lock(context.streams.at(sindex).streamMutex);
      auto* const sample = samplesNeeded ? &samples[sindex] : nullptr;
      auto& sampleMeta = samplesMeta[sindex];
      if (stream.second.size() > 0) {
        size_t length = 0;
        auto& sampleMap = context.streams.at(sindex).sampleMap;
        const uint32_t sampleSize = context.streams.at(sindex).config.sampleSizeInBytes;
        sampleMeta.references.resize(stream.second.size());
        size_t ridx = 0;
        for (auto& r : stream.second) {
          if (sampleMap.find(r.buffer_tagged.sequence_number) == sampleMap.end()) {
            XR_LOGD(
                "Subaligner::processManifests - Attempted to close a reference for which we've "
                "don't have a sample.");
            return;
          }
          sampleMeta.references[ridx].timestamp =
              sampleMap[r.buffer_tagged.sequence_number].metadata->header.timestamp;
          sampleMeta.references[ridx].sequenceNumber =
              sampleMap[r.buffer_tagged.sequence_number].metadata->header.sequenceNumber;
          sampleMeta.references[ridx].subSampleOffset = r.nrbytes_offset / sampleSize;
          sampleMeta.references[ridx].numSubSamples = r.nrbytes_length / sampleSize;
          length += r.nrbytes_length;
          std::string sequenceString = std::to_string(r.buffer_tagged.sequence_number);
          // Copy full history
          if (sample) {
            sample->metadata->history["subaligner_" + sequenceString] =
                sampleMap[r.buffer_tagged.sequence_number].metadata;
            sample->metadata->processingStamps["subaligner_" + sequenceString + "_start"] =
                sampleMap[r.buffer_tagged.sequence_number]
                    .metadata->processingStamps["subaligner_start"];
          }
          ++ridx;
        }
        uint8_t* ptr = nullptr;
        if (sample) {
          // allocate buffer for the output "flattened" sample
          sample->parameters = sampleMap[stream.second[0].buffer_tagged.sequence_number].parameters;
          sample->numberOfSubSamples = length / sampleSize;
          sample->payload = Framework::instance().memoryPool()->getBufferFromPool(
              streams_.at(sindex).streamID, length);
          ptr = ((CpuBuffer)sample->payload).get();
        }
        for (auto& r : stream.second) {
          if (ptr) {
            std::copy(
                r.buffer_tagged.buffer_durational.buffer.get() + r.nrbytes_offset,
                r.buffer_tagged.buffer_durational.buffer.get() + r.nrbytes_offset +
                    r.nrbytes_length,
                ptr);
            ptr += r.nrbytes_length;
          }

          if (r.nrbytes_offset + r.nrbytes_length ==
                  (r.buffer_tagged.nrsamples_total * sampleSize) &&
              sampleMap.find(r.buffer_tagged.sequence_number) != sampleMap.end()) {
            sampleMap.erase(r.buffer_tagged.sequence_number);
          }
        }
        // finalize sample header, first sample might be partial, compensate for the potential
        // offset
        const double samplePeriod = 1.0 / stream.second[0].buffer_tagged.sample_rate;
        const double sample_timestamp =
            stream.second[0].buffer_tagged.buffer_durational.duration.start_time +
            double(stream.second[0].nrbytes_offset / sampleSize) * samplePeriod;
        double sample_duration = double(length) / sampleSize * samplePeriod;
        if (sample) {
          sample->metadata->header.sequenceNumber = streams_.at(sindex).sequenceOut++;
          sample->metadata->header.timestamp = sample_timestamp;
        }
        // effective computed duration of the manifest for this sample
        sampleMeta.timestamp = sample_timestamp;
        sampleMeta.duration = sample_duration;
      }
    }
    // Check configs and execute
    if (!context.configured) {
      std::vector<StreamConfig> configs;
      configs.reserve(context.streams.size());
      AlignerConfigsMeta configsMeta;
      configsMeta.reserve(context.streams.size());
      size_t idx = 0;
      for (const auto& stream : context.streams) {
        configs.push_back(stream.second.config);
        configsMeta.push_back(
            AlignerStreamMeta{streams_[idx].streamID, stream.second.config.sampleSizeInBytes});
        idx++;
      }
      if (configs.size() == streams_.size()) {
        inhibitSampleCallback_ = !alignedConfigCallback(configs);
        context.configured = true;
        alignedConfigsMetaCallback(configsMeta);
      }
    }

    if (!inhibitSampleCallback_) {
      alignedSamplesMetaCallback(samplesMeta);
      if (samplesNeeded) {
        const auto seconds = NOW();
        for (const auto& sample : samples) {
          sample.metadata->processingStamps["subaligner_end"] = seconds;
        }
        alignedCallback(samples);
      }
    }
  }
}

void SubAligner::enroll(
    size_t idx,
    const StreamConfig& config,
    AlignerContext& context,
    const std::lock_guard<std::mutex>&) {
  std::lock_guard<std::mutex> lock(context.implMutex);

  // Get time offset and metronome
  double offset = 0.0;
  bool metronome = defaultUseMetronome_;
  if (settings_.size() > idx) {
    offset = settings_[idx].timeOffset;
    metronome = settings_[idx].useMetronome;
  }

  // Override with any hints
  if (settingHints_.find(streams_[idx].streamID) != settingHints_.end()) {
    const auto& sid = streams_[idx].streamID;
    offset = settingHints_[sid].timeOffset;
    metronome = settingHints_[sid].useMetronome;
  }

  auto& streamData = context.streams[idx];
  // Enroll in aligner and store interface
  streamData.interface = context.impl->enroll(
      (config.sampleSizeInBytes != 0 ? config.sampleSizeInBytes : 1),
      metronome ? config.nominalSampleRate : 0.0,
      -offset);
  XR_LOGT(
      "Enrolling {} @ {:.3f} fps, {}using metronome.",
      streams_[idx].streamID,
      config.nominalSampleRate,
      metronome ? "" : "NOT ");

  context.lookupIndex[context.streams[idx].interface->index()] = idx;
  // Store config
  streamData.config = config;

  if (0 == idx) {
    context.streams[idx].interface->primarize();
    if (config.nominalSampleRate > 0.0) {
      finalizeStrategy_ = 0.5 * config.nominalSampleRate + getMaxLatencyOffset();
    }
  }
}

void SubAligner::sampleCallback(size_t idx, const StreamSample& sample) {
  int activeContext;
  {
    std::lock_guard<std::mutex> lock(globalMutex_);

    activeContext = streams_[idx].activeContext;

    // Force everything onto the latest context, for the case where not all streams are
    // reconfigured simultaneously
    // Note: It may be better to estimate start/end-times for the contexts to determine
    if (activeContext < latestContext_) {
      auto& config = contexts_[activeContext].streams[idx].config;
      streams_[idx].activeContext = latestContext_;
      activeContext = latestContext_;
      auto& context = contexts_.at(activeContext);
      enroll(idx, config, context, lock);
    }
  }

  auto& context = contexts_.at(activeContext);

  if (std::holds_alternative<PrimarySelection>(finalizeStrategy_) &&
      !std::get<PrimarySelection>(finalizeStrategy_)
           .isWithinTolerance(sample.metadata->header.timestamp)) {
    XR_LOGW_EVERY_N_SEC(
        5,
        "Too old sample arrived on stream: #{}, '{}', stamp: {}, tolerance: {}",
        idx,
        streams_[idx].streamID.c_str(),
        sample.metadata->header.timestamp,
        std::get<PrimarySelection>(finalizeStrategy_).maxLatencySeconds);
    // dump sample
    return;
  }

  // feed underlying aligner
  {
    sample.metadata->processingStamps["subaligner_start"] = NOW();
    const auto alignerLock = std::scoped_lock(context.implMutex, context.streams[idx].streamMutex);
    // Store the sample data
    const uint32_t seq = context.streams[idx].sequenceIn++;
    context.streams[idx].sampleMap[seq] = sample;
    if (!hasSampleCallback()) {
      // Drop payload: we don't need to carry this buffer around for alignment, since
      // we won't look at it later.
      context.streams[idx].sampleMap[seq].payload = nullptr;
    }

    // Feed data in aligner, but act only on the "metadata" as the references are already held by
    // sampleMap
    const size_t buffer_size =
        sample.numberOfSubSamples * context.streams[idx].config.sampleSizeInBytes;

    // If the sampling rate for a stream is unknown, propose an end time that's 1ms
    // in the future. I'm not sure why this is necessary, since it seems this should
    // be something handled by the aligner itself. But, it's a carry over from the
    // ArgentCapture library, where this exact computation was done for data without
    // a sampling rate (vision pose, rendered pose, IMU, etc.)
    //
    // Without this end time computation, we cannot align streams that don't have a
    // known sampling rate. This does nothing when the sample rate for a stream is
    // known, since the default behavior of feed() is to inline -1.0 for the end time.
    const double endTime = (0.0 == context.streams[idx].config.nominalSampleRate)
        ? (sample.metadata->header.timestamp + 0.001)
        : -1.0;

    context.streams[idx].interface->feed(
        hasSampleCallback() ? (CpuBuffer)sample.payload : nullptr,
        buffer_size,
        sample.metadata->header.timestamp,
        endTime);
  }

  {
    std::lock_guard<std::mutex> lock(context.implMutex);

    // If there's no primary stream, finalize all streams that are determined to be
    // lagging given the current sample timestamp. If there IS a primary stream,
    // finalize all streams that are determined to be lagging given the primary stream's
    // latest sample.
    if (std::holds_alternative<GlobalMaxLatency>(finalizeStrategy_)) {
      const double maxLatency = std::get<GlobalMaxLatency>(finalizeStrategy_);
      context.impl->finalizeBefore(sample.metadata->header.timestamp - maxLatency);
    } else {
      auto& primarySelection = std::get<PrimarySelection>(finalizeStrategy_);
      context.impl->finalizeBefore(
          sample.metadata->header.timestamp - primarySelection.maxLatencySeconds);
      primarySelection.setReference(sample.metadata->header.timestamp);
    }
  }
  if (policy_ == ThreadPolicy::THREAD_NEUTRAL) {
    align();
  }
}

bool SubAligner::configCallback(size_t idx, const StreamConfig& config) {
  std::lock_guard<std::mutex> lock(globalMutex_);
  int activeContext = streams_[idx].activeContext + 1;
  streams_[idx].activeContext = activeContext;

  // If an aligner doesn't exist for the new context, make it
  if (contexts_.find(activeContext) == contexts_.end()) {
    contexts_[activeContext].impl = std::make_unique<subaligner::Aligner>();
    latestContext_ = std::max(activeContext, latestContext_);
  }
  auto& context = contexts_.at(activeContext);

  enroll(idx, config, context, lock);

  return true;
}

void SubAligner::clear() {
  const std::lock_guard<std::mutex> globalLock(globalMutex_);
  for (auto& [_, context] : contexts_) {
    const std::lock_guard<std::mutex> implLock(context.implMutex);
    context.impl->finalize();
    context.impl->align();
    context.impl->retrieve();
    for (auto& [_, streamContext] : context.streams) {
      const std::lock_guard<std::mutex> streamLock(streamContext.streamMutex);
      streamContext.sampleMap.clear();
    }
  }
}

std::optional<PrimaryAlignmentStream::Election> PrimaryAlignmentStream::bestImageStream(
    const SubAligner& aligner,
    const std::vector<StreamID>& streamIDs,
    double maxLatencyFraction) {
  std::unordered_map<StreamID, StreamConfig> imageStreamConfigs;
  const auto imageType = cthulhu::Framework::instance().typeRegistry()->findTypeName("Image");
  for (const auto& streamID : streamIDs) {
    if (const auto stream = cthulhu::Framework::instance().streamRegistry()->getStream(streamID);
        stream && stream->description().type() == imageType->typeID()) {
      if (!aligner.isRegistered(streamID)) {
        const auto msg = fmt::format(
            "Stream ID '{}' is up for primary image stream election, but it's unknown to the aligner. "
            "Ensure that the stream is registered with the aligner",
            streamID);
        XR_LOGE("{}", msg);
        throw std::runtime_error(msg);
      } else {
        imageStreamConfigs[streamID] = stream->config();
      }
    }
  }

  if (imageStreamConfigs.empty()) {
    return std::nullopt;
  }

  // Dereference OK; guaranteed to have at least one element
  const auto& [streamID, config] = *std::min_element(
      imageStreamConfigs.cbegin(),
      imageStreamConfigs.cend(),
      [](const auto& left, const auto& right) {
        return left.second.nominalSampleRate < right.second.nominalSampleRate;
      });

  if (0.0 == config.nominalSampleRate) {
    const auto msg = fmt::format(
        "Stream ID '{}' has a sample rate of zero! We can't compute the allowable offset from that.");
    XR_LOGE("{}", msg);
    throw std::runtime_error(msg);
  }
  const double maxLatencyOffset =
      maxLatencyFraction * (1.0 / config.nominalSampleRate) + aligner.getMaxLatencyOffset();

  return PrimaryAlignmentStream::Election{streamID, maxLatencyOffset};
}

} // namespace cthulhu
