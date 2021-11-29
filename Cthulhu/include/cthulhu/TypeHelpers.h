#pragma once

#include <array>
#include <string>
#include <type_traits>
#include <vector>

namespace cthulhu {

template <class T>
std::string typeString();

#define TYPE_STRING_DECLARE(x) \
  template <>                  \
  std::string typeString<x>();

TYPE_STRING_DECLARE(bool)
TYPE_STRING_DECLARE(char)
TYPE_STRING_DECLARE(double)
TYPE_STRING_DECLARE(float)
TYPE_STRING_DECLARE(int64_t)
TYPE_STRING_DECLARE(uint64_t)
TYPE_STRING_DECLARE(int32_t)
TYPE_STRING_DECLARE(uint32_t)
TYPE_STRING_DECLARE(int16_t)
TYPE_STRING_DECLARE(uint16_t)
TYPE_STRING_DECLARE(int8_t)
TYPE_STRING_DECLARE(uint8_t)

template <class T, typename std::enable_if<std::is_enum<T>::value>::type* = nullptr>
std::string typeStringFilter() {
  return typeString<typename std::underlying_type<T>::type>();
}

template <
    class T,
    typename std::enable_if<!std::is_array<T>::value && !std::is_enum<T>::value>::type* = nullptr>
std::string typeStringFilter() {
  return typeString<T>();
}

template <typename>
struct ArrayTrait;

template <typename T>
struct ArrayTrait {
  using type = T;
  static constexpr size_t size = 1;
};

template <typename T, size_t N>
struct ArrayTrait<T[N]> {
  using type = T;
  static constexpr size_t size = N;
};

template <typename T, size_t N>
struct ArrayTrait<std::array<T, N>> {
  using type = T;
  static constexpr size_t size = N;
};

template <typename T, size_t N, size_t M>
struct ArrayTrait<T[N][M]> {
  using type = T;
  static constexpr size_t size = N * M;
};

template <typename T, size_t N, size_t M>
struct ArrayTrait<std::array<std::array<T, M>, N>> {
  using type = T;
  static constexpr size_t size = N * M;
};

template <typename T, typename Alloc>
struct ArrayTrait<std::vector<T, Alloc>> {
  using type = T;
  // size intentionally skipped; you should never see that it's missing...
  // Dynamically-sized types are handled differently. We cannot know their size
  // at compile time. Hence, there's no size to expose here.
};

template <>
struct ArrayTrait<std::string> {
  using type = std::string::value_type;
  // size intentionally skipped; you should never see that it's missing...
  // Dynamically-sized types are handled differently. We cannot know their size
  // at compile time. Hence, there's no size to expose here.
};

template <class T>
std::string typeName() {
  return typeStringFilter<typename ArrayTrait<T>::type>();
}

template <class T>
size_t typeSize() {
  return ArrayTrait<T>::size;
}

} // namespace cthulhu
