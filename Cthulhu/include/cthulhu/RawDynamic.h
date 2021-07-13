// Copyright 2004-present Facebook. All Rights Reserved.

#pragma once

#include <cstring>
#include <memory>
#include <string_view>
#include <vector>

#include <cthulhu/BufferTypes.h>

namespace cthulhu {

// RawDynamic is a generic holder around dynamically-sized data.
// The data may be viewed as any vector of T, or as a string view.
// RawDynamic remembers a variant of the element type by tracking
// the element size.
//
// RawDynamic is templated over the raw memory representation. By
// default, it's a shared pointer. RawDynamic may be templated with
// an IPC smart pointer variant.
template <class Raw = CpuBuffer>
class RawDynamic {
 public:
  RawDynamic() = default;
  RawDynamic(RawDynamic&&) = default;
  RawDynamic& operator=(RawDynamic&&) = default;
  RawDynamic(const RawDynamic&) = default;
  RawDynamic& operator=(const RawDynamic&) = default;

  // Note: ctor only valid for CpuBuffer Raw type argument
  template <typename T>
  explicit RawDynamic(const std::vector<T>& vec)
      : elementCount(vec.size()), elementSize(sizeof(T)), raw(getBuffer()) {
    static_assert(std::is_pod_v<T>, "RawDynamic will only work well with POD elements!");
    std::memcpy(raw.get(), vec.data(), size());
  }

  // Note: ctor only valid for CpuBuffer Raw type argument
  explicit RawDynamic(
      std::string_view str,
      size_t elementSize = sizeof(std::string_view::value_type))
      : elementCount(str.size() / elementSize), elementSize(elementSize), raw(getBuffer()) {
    std::memcpy(raw.get(), str.data(), size());
  }

  // Note: ctor only valid for CpuBuffer Raw type argument
  explicit RawDynamic(CpuBuffer& buf, size_t count);

  inline size_t size() const {
    return elementCount * elementSize;
  }

  // Returns a string view of the memory, regardless of whether or not the raw dynamic
  // was constructed with a string.
  const std::string_view asString() const {
    return std::string_view(reinterpret_cast<char*>(raw.get()), size());
  }

  // Returns a copy of the data represented as a vector of Ts.
  template <typename T>
  std::vector<T> copyAs() const {
    const T* begin = reinterpret_cast<T*>(raw.get());
    const T* end = begin + (size() / sizeof(T));
    return std::vector<T>(begin, end);
  }

  friend bool operator==(const RawDynamic& lhs, const RawDynamic& rhs) {
    if ((nullptr == lhs.raw) && (nullptr == rhs.raw)) {
      return true;
    }
    return lhs.raw && rhs.raw && (lhs.elementCount == rhs.elementCount) &&
        (lhs.elementSize == rhs.elementSize) &&
        (0 == std::memcmp(lhs.raw.get(), rhs.raw.get(), lhs.size()));
  }

  friend bool operator!=(const RawDynamic& lhs, const RawDynamic& rhs) {
    return !(lhs == rhs);
  }

  explicit operator bool() const {
    return (nullptr != raw);
  }

  // Courtesy of Jo Boccara
  // https://www.fluentcpp.com/2018/05/18/make-sfinae-pretty-2-hidden-beauty-sfinae/
  //
  // I'm hiding this clone() function when we're not using a standard CpuBuffer as
  // the backing memory because we don't have a way to use the correct allocator otherwise.
  template <typename Raw_ = Raw, typename = std::enable_if_t<std::is_same_v<Raw_, CpuBuffer>>>
  RawDynamic<Raw_> clone() const {
    RawDynamic<Raw_> copy;
    copy.elementCount = elementCount;
    copy.elementSize = elementSize;
    copy.raw = getBuffer();
    std::memcpy(copy.raw.get(), raw.get(), size());

    return copy;
  }

  // Total number of elements of the raw data
  size_t elementCount = 0;
  // Single element size of the raw data
  size_t elementSize = 0;
  // The raw data
  Raw raw;

 private:
  CpuBuffer getBuffer() const;
};

using SharedRawDynamicArray = std::shared_ptr<RawDynamic<>>;
static inline SharedRawDynamicArray makeSharedRawDynamicArray(size_t count) {
  return std::shared_ptr<RawDynamic<>>(
      new RawDynamic<>[count](), std::default_delete<RawDynamic<>[]>());
}

} // namespace cthulhu
