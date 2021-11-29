


/**
 * Note: This file is forked from boost/interprocess/detail/managed_open_or_create_impl.hpp
 * It provides a version of the templates that are usable by our android implementation of
 * managed shared memory, by modifying the 3rd argument of the MappedRegion c'tor in line 291 and
 * 338.
 */

//////////////////////////////////////////////////////////////////////////////
//
// (C) Copyright Ion Gaztanaga 2006-2012. Distributed under the Boost
// Software License, Version 1.0. (See accompanying file
// LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
//
// See http://www.boost.org/libs/interprocess for documentation.
//
//////////////////////////////////////////////////////////////////////////////

#ifndef BOOST_INTERPROCESS_MANAGED_OPEN_OR_CREATE_IMPL_ASHMEM
#define BOOST_INTERPROCESS_MANAGED_OPEN_OR_CREATE_IMPL_ASHMEM

#ifndef BOOST_CONFIG_HPP
#include <boost/config.hpp>
#endif
#
#if defined(BOOST_HAS_PRAGMA_ONCE)
#pragma once
#endif

#include <boost/interprocess/detail/managed_open_or_create_impl.hpp>

namespace boost {
namespace interprocess {

namespace ipcdetail {

template <class DeviceAbstraction, std::size_t MemAlignment, bool FileBased, bool StoreDevice>
class managed_open_or_create_impl_ashmem
    : public managed_open_or_create_impl_device_holder<StoreDevice, DeviceAbstraction> {
  // Non-copyable
  BOOST_MOVABLE_BUT_NOT_COPYABLE(managed_open_or_create_impl_ashmem)

  typedef typename managed_open_or_create_impl_device_id_t<DeviceAbstraction>::type device_id_t;
  typedef managed_open_or_create_impl_device_holder<StoreDevice, DeviceAbstraction> DevHolder;
  enum { UninitializedSegment, InitializingSegment, InitializedSegment, CorruptedSegment };

 public:
  static const std::size_t ManagedOpenOrCreateUserOffset = ct_rounded_size <
      sizeof(boost::uint32_t),
                           MemAlignment
      ? (MemAlignment)
      : (::boost::container::dtl::alignment_of<::boost::container::dtl::max_align_t>::value) >
          ::value;

  managed_open_or_create_impl_ashmem() {}

  managed_open_or_create_impl_ashmem(
      create_only_t,
      const device_id_t& id,
      std::size_t size,
      mode_t mode,
      const void* addr) {
    priv_open_or_create(DoCreate, id, size, mode, addr, null_mapped_region_function());
  }

  managed_open_or_create_impl_ashmem(
      open_only_t,
      const device_id_t& id,
      mode_t mode,
      const void* addr) {
    priv_open_or_create(DoOpen, id, 0, mode, addr, null_mapped_region_function());
  }

  managed_open_or_create_impl_ashmem(
      open_or_create_t,
      const device_id_t& id,
      std::size_t size,
      mode_t mode,
      const void* addr) {
    priv_open_or_create(DoOpenOrCreate, id, size, mode, addr, null_mapped_region_function());
  }

  template <class ConstructFunc>
  managed_open_or_create_impl_ashmem(
      create_only_t,
      const device_id_t& id,
      std::size_t size,
      mode_t mode,
      const void* addr,
      const ConstructFunc& construct_func) {
    priv_open_or_create(DoCreate, id, size, mode, addr, construct_func);
  }

  template <class ConstructFunc>
  managed_open_or_create_impl_ashmem(
      open_only_t,
      const device_id_t& id,
      mode_t mode,
      const void* addr,
      const ConstructFunc& construct_func) {
    priv_open_or_create(DoOpen, id, 0, mode, addr, construct_func);
  }

  template <class ConstructFunc>
  managed_open_or_create_impl_ashmem(
      open_or_create_t,
      const device_id_t& id,
      std::size_t size,
      mode_t mode,
      const void* addr,
      const ConstructFunc& construct_func) {
    priv_open_or_create(DoOpenOrCreate, id, size, mode, addr, construct_func);
  }

  managed_open_or_create_impl_ashmem(BOOST_RV_REF(managed_open_or_create_impl_ashmem) moved) {
    this->swap(moved);
  }

  managed_open_or_create_impl_ashmem& operator=(BOOST_RV_REF(managed_open_or_create_impl_ashmem)
                                                    moved) {
    managed_open_or_create_impl_ashmem tmp(boost::move(moved));
    this->swap(tmp);
    return *this;
  }

  ~managed_open_or_create_impl_ashmem() {}

  std::size_t get_user_size() const {
    return m_mapped_region.get_size() - ManagedOpenOrCreateUserOffset;
  }

  void* get_user_address() const {
    return static_cast<char*>(m_mapped_region.get_address()) + ManagedOpenOrCreateUserOffset;
  }

  std::size_t get_real_size() const {
    return m_mapped_region.get_size();
  }

  void* get_real_address() const {
    return m_mapped_region.get_address();
  }

  void swap(managed_open_or_create_impl_ashmem& other) {
    this->m_mapped_region.swap(other.m_mapped_region);
  }

  bool flush() {
    return m_mapped_region.flush();
  }

  const mapped_region& get_mapped_region() const {
    return m_mapped_region;
  }

  DeviceAbstraction& get_device() {
    return this->DevHolder::get_device();
  }

  const DeviceAbstraction& get_device() const {
    return this->DevHolder::get_device();
  }

 private:
  // These are templatized to allow explicit instantiations
  template <bool dummy>
  static void truncate_device(DeviceAbstraction&, offset_t, false_) {} // Empty

  template <bool dummy>
  static void truncate_device(DeviceAbstraction& dev, offset_t size, true_) {
    dev.truncate(size);
  }

  template <bool dummy>
  static bool check_offset_t_size(std::size_t, false_) {
    return true;
  } // Empty

  template <bool dummy>
  static bool check_offset_t_size(std::size_t size, true_) {
    return size == std::size_t(offset_t(size));
  }

  // These are templatized to allow explicit instantiations
  template <bool dummy>
  static void
  create_device(DeviceAbstraction& dev, const device_id_t& id, std::size_t size, false_ file_like) {
    (void)file_like;
    DeviceAbstraction tmp(create_only, id, read_write, size);
    tmp.swap(dev);
  }

  template <bool dummy>
  static void
  create_device(DeviceAbstraction& dev, const device_id_t& id, std::size_t, true_ file_like) {
    (void)file_like;
    DeviceAbstraction tmp(create_only, id, read_write);
    tmp.swap(dev);
  }

  template <class ConstructFunc>
  inline void priv_open_or_create(
      create_enum_t type,
      const device_id_t& id,
      std::size_t size,
      mode_t mode,
      const void* addr,
      ConstructFunc construct_func) {
    typedef bool_<FileBased> file_like_t;
    (void)mode;
    bool created = false;
    bool ronly = false;
    bool cow = false;
    DeviceAbstraction dev;

    if (type != DoOpen) {
      // Check if the requested size is enough to build the managed metadata
      const std::size_t func_min_size = construct_func.get_min_size();
      if ((std::size_t(-1) - ManagedOpenOrCreateUserOffset) < func_min_size ||
          size < (func_min_size + ManagedOpenOrCreateUserOffset)) {
        throw interprocess_exception(error_info(size_error));
      }
    }
    // Check size can be represented by offset_t (used by truncate)
    if (type != DoOpen && !check_offset_t_size<FileBased>(size, file_like_t())) {
      throw interprocess_exception(error_info(size_error));
    }
    if (type == DoOpen && mode == read_write) {
      DeviceAbstraction tmp(open_only, id, read_write);
      tmp.swap(dev);
      created = false;
    } else if (type == DoOpen && mode == read_only) {
      DeviceAbstraction tmp(open_only, id, read_only);
      tmp.swap(dev);
      created = false;
      ronly = true;
    } else if (type == DoOpen && mode == copy_on_write) {
      DeviceAbstraction tmp(open_only, id, read_only);
      tmp.swap(dev);
      created = false;
      cow = true;
    } else if (type == DoCreate) {
      create_device<FileBased>(dev, id, size, file_like_t());
      created = true;
    } else if (type == DoOpenOrCreate) {
      // This loop is very ugly, but brute force is sometimes better
      // than diplomacy. If someone knows how to open or create a
      // file and know if we have really created it or just open it
      // drop me a e-mail!
      bool completed = false;
      spin_wait swait;
      while (!completed) {
        try {
          create_device<FileBased>(dev, id, size, file_like_t());
          created = true;
          completed = true;
        } catch (interprocess_exception& ex) {
          if (ex.get_error_code() != already_exists_error) {
            throw;
          } else {
            try {
              DeviceAbstraction tmp(open_only, id, read_write);
              dev.swap(tmp);
              created = false;
              completed = true;
            } catch (interprocess_exception& e) {
              if (e.get_error_code() != not_found_error) {
                throw;
              }
            } catch (...) {
              throw;
            }
          }
        } catch (...) {
          throw;
        }
        swait.yield();
      }
    }

    if (created) {
      try {
        // If this throws, we are lost
        truncate_device<FileBased>(dev, size, file_like_t());

        // If the following throws, we will truncate the file to 1
        mapped_region region(dev, read_write, 0, size, addr);
        boost::uint32_t* patomic_word = 0; // avoid gcc warning
        patomic_word = static_cast<boost::uint32_t*>(region.get_address());
        boost::uint32_t previous =
            atomic_cas32(patomic_word, InitializingSegment, UninitializedSegment);

        if (previous == UninitializedSegment) {
          try {
            construct_func(
                static_cast<char*>(region.get_address()) + ManagedOpenOrCreateUserOffset,
                size - ManagedOpenOrCreateUserOffset,
                true);
            // All ok, just move resources to the external mapped region
            m_mapped_region.swap(region);
          } catch (...) {
            atomic_write32(patomic_word, CorruptedSegment);
            throw;
          }
          atomic_write32(patomic_word, InitializedSegment);
        } else if (previous == InitializingSegment || previous == InitializedSegment) {
          throw interprocess_exception(error_info(already_exists_error));
        } else {
          throw interprocess_exception(error_info(corrupted_error));
        }
      } catch (...) {
        try {
          truncate_device<FileBased>(dev, 1u, file_like_t());
        } catch (...) {
        }
        throw;
      }
    } else {
      if (FileBased) {
        offset_t filesize = 0;
        spin_wait swait;
        while (filesize == 0) {
          if (!get_file_size(file_handle_from_mapping_handle(dev.get_mapping_handle()), filesize)) {
            error_info err = system_error_code();
            throw interprocess_exception(err);
          }
          swait.yield();
        }
        if (filesize == 1) {
          throw interprocess_exception(error_info(corrupted_error));
        }
      }

      mapped_region region(
          dev, ronly ? read_only : (cow ? copy_on_write : read_write), 0, size, addr);

      boost::uint32_t* patomic_word = static_cast<boost::uint32_t*>(region.get_address());
      boost::uint32_t value = atomic_read32(patomic_word);

      spin_wait swait;
      while (value == InitializingSegment || value == UninitializedSegment) {
        swait.yield();
        value = atomic_read32(patomic_word);
      }

      if (value != InitializedSegment)
        throw interprocess_exception(error_info(corrupted_error));

      construct_func(
          static_cast<char*>(region.get_address()) + ManagedOpenOrCreateUserOffset,
          region.get_size() - ManagedOpenOrCreateUserOffset,
          false);
      // All ok, just move resources to the external mapped region
      m_mapped_region.swap(region);
    }
    if (StoreDevice) {
      this->DevHolder::get_device() = boost::move(dev);
    }
  }

  friend void swap(
      managed_open_or_create_impl_ashmem& left,
      managed_open_or_create_impl_ashmem& right) {
    left.swap(right);
  }

 private:
  friend class interprocess_tester;
  void dont_close_on_destruction() {
    interprocess_tester::dont_close_on_destruction(m_mapped_region);
  }

  mapped_region m_mapped_region;
};

} // namespace ipcdetail

} // namespace interprocess
} // namespace boost

#include <boost/interprocess/detail/config_end.hpp>

#endif //#ifndef BOOST_INTERPROCESS_MANAGED_OPEN_OR_CREATE_IMPL_ASHMEM
