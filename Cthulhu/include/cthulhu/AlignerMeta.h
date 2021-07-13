// Copyright 2004-present Facebook. All Rights Reserved.

#pragma once

#include <cthulhu/StreamInterface.h>

#include <sstream>

namespace cthulhu {

struct AlignerStreamMeta {
  cthulhu::StreamID streamID;
  uint32_t subSampleSize;
};

using AlignerConfigsMeta = std::vector<AlignerStreamMeta>;

struct AlignerReferenceMeta {
  double timestamp;
  uint32_t sequenceNumber;
  uint32_t subSampleOffset; // In sub-samples
  uint32_t numSubSamples; // In sub-samples
};

struct AlignerSampleMeta {
  double timestamp;
  double duration;
  std::vector<AlignerReferenceMeta> references;
};

using AlignerSamplesMeta = std::vector<AlignerSampleMeta>;

void serialize(const AlignerConfigsMeta& input, std::ostringstream& output);

void serialize(const AlignerSamplesMeta& input, std::ostringstream& output);

void deserialize(std::istringstream& input, AlignerConfigsMeta& output);

void deserialize(std::istringstream& input, AlignerSamplesMeta& output);

} // namespace cthulhu
