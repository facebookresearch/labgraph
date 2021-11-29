#include <memory>

#include <cthulhu/StreamConfigEquality.h>

namespace cthulhu {

bool streamConfigsEqual(
    const StreamConfig& lhs,
    const StreamConfig& rhs,
    const TypeInfoInterface& stream_type_info) {
  if (lhs.nominalSampleRate != rhs.nominalSampleRate) {
    return false;
  }
  if (lhs.sampleSizeInBytes != rhs.sampleSizeInBytes) {
    return false;
  }
  if (stream_type_info.configParameterSize() > 0) {
    if (std::memcmp(
            lhs.parameters.get(), rhs.parameters.get(), stream_type_info.configParameterSize()) !=
        0) {
      return false;
    }
  }
  if (stream_type_info.configNumberDynamicFields() > 0) {
    for (int i = 0; i < stream_type_info.configNumberDynamicFields(); ++i) {
      const auto& lhs_raw_dynamic = *(lhs.dynamicParameters.get() + i);
      const auto& rhs_raw_dynamic = *(rhs.dynamicParameters.get() + i);
      if (lhs_raw_dynamic != rhs_raw_dynamic) {
        return false;
      }
    }
  }
  return true;
}

} // namespace cthulhu
