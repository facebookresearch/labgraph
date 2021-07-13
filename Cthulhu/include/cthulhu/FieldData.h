// Copyright 2004-present Facebook. All Rights Reserved.

#pragma once

#include <limits>
#include <map>
#include <numeric>
#include <string>
#include <string_view>
#include <vector>

namespace cthulhu {

struct Field {
  uint32_t offset = 0;
  uint32_t size = 0;
  std::string typeName;
  uint32_t numElements = 0;

  // Describes whether or not a field is dynamically-sized.
  // If it is, the 'offset' member describes its allocation
  // in an array of dynamically-sized arrays. Otherwise, 'offset'
  // describes its offset in the parameters block.
  bool isDynamic = false;

  friend bool operator==(const Field& left, const Field& right) {
    return (left.offset == right.offset) && (left.size == right.size) &&
        (left.typeName == right.typeName) && (left.numElements == right.numElements) &&
        (left.isDynamic == right.isDynamic);
  }

  friend bool operator!=(const Field& left, const Field& right) {
    return !(left == right);
  }

}; // namespace cthulhu

// Some consumers need to be able to iterate in sorted order.
using FieldData = std::map<std::string, Field>;

} // namespace cthulhu
