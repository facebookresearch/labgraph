
#include <cthulhu/TypeHelpers.h>

namespace cthulhu {

#define TYPE_STRING_DEFINE(x)   \
  template <>                   \
  std::string typeString<x>() { \
    return #x;                  \
  }

TYPE_STRING_DEFINE(bool)
TYPE_STRING_DEFINE(char)
TYPE_STRING_DEFINE(double)
TYPE_STRING_DEFINE(float)
TYPE_STRING_DEFINE(int64_t)
TYPE_STRING_DEFINE(uint64_t)
TYPE_STRING_DEFINE(int32_t)
TYPE_STRING_DEFINE(uint32_t)
TYPE_STRING_DEFINE(int16_t)
TYPE_STRING_DEFINE(uint16_t)
TYPE_STRING_DEFINE(int8_t)
TYPE_STRING_DEFINE(uint8_t)

} // namespace cthulhu
