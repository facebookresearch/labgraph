// Copyright 2004-present Facebook. All Rights Reserved.

#include <cthulhu/AlignerMeta.h>

namespace cthulhu {

void serialize(const AlignerConfigsMeta& input, std::ostringstream& output) {
  uint32_t size = input.size();
  output.write((char*)&size, sizeof(uint32_t));
  for (const auto& in : input) {
    uint8_t length = in.streamID.length();
    output.write((char*)&length, sizeof(uint8_t));
    output.write((char*)&(in.streamID[0]), in.streamID.length());
    output.write((char*)&in.subSampleSize, sizeof(uint32_t));
  }
}

void serialize(const AlignerSamplesMeta& input, std::ostringstream& output) {
  uint32_t size = input.size();
  output.write((char*)&size, sizeof(uint32_t));
  for (const auto& in : input) {
    output.write((char*)&in.timestamp, sizeof(double));
    uint32_t refs = in.references.size();
    output.write((char*)&refs, sizeof(uint32_t));
    for (const auto& ref : in.references) {
      output.write((char*)&ref.sequenceNumber, sizeof(uint32_t));
      output.write((char*)&ref.subSampleOffset, sizeof(uint32_t));
      output.write((char*)&ref.numSubSamples, sizeof(uint32_t));
    }
  }
}

void deserialize(std::istringstream& input, AlignerConfigsMeta& output) {
  uint32_t size;
  input.read((char*)&size, sizeof(uint32_t));
  output.resize(size);
  for (uint32_t in = 0; in < size; ++in) {
    uint8_t length;
    input.read((char*)&length, sizeof(uint8_t));
    output[in].streamID.resize(length);
    input.read((char*)&(output[in].streamID[0]), length);
    input.read((char*)&(output[in].subSampleSize), sizeof(uint32_t));
  }
}

void deserialize(std::istringstream& input, AlignerSamplesMeta& output) {
  uint32_t size;
  input.read((char*)&size, sizeof(uint32_t));
  output.resize(size);
  for (uint32_t in = 0; in < size; ++in) {
    input.read((char*)&output[in].timestamp, sizeof(double));
    uint32_t refs;
    input.read((char*)&refs, sizeof(uint32_t));
    output[in].references.resize(refs);
    for (uint32_t ref = 0; ref < refs; ++ref) {
      input.read((char*)&(output[in].references[ref].sequenceNumber), sizeof(uint32_t));
      input.read((char*)&(output[in].references[ref].subSampleOffset), sizeof(uint32_t));
      input.read((char*)&(output[in].references[ref].numSubSamples), sizeof(uint32_t));
    }
  }
}

} // namespace cthulhu
