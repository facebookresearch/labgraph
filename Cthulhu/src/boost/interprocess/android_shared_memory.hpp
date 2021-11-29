#ifndef BOOST_INTERPROCESS_ANDROID_SHARED_MEMORY_HPP
#define BOOST_INTERPROCESS_ANDROID_SHARED_MEMORY_HPP

#ifndef BOOST_CONFIG_HPP
#include <boost/config.hpp>
#endif

#if defined(BOOST_HAS_PRAGMA_ONCE)
#pragma once
#endif

#include <boost/interprocess/creation_tags.hpp>
#include <boost/interprocess/detail/config_begin.hpp>
#include <boost/interprocess/detail/os_file_functions.hpp>
#include <boost/interprocess/detail/shared_dir_helpers.hpp>
#include <boost/interprocess/detail/workaround.hpp>
#include <boost/interprocess/exceptions.hpp>
#include <boost/interprocess/interprocess_fwd.hpp>
#include <boost/move/adl_move_swap.hpp>
#include <boost/move/utility_core.hpp>
#include <cstddef>
#include <string>

#include <android/sharedmem.h>
#include <fcntl.h>
#include <linux/ashmem.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <unistd.h>

//!\file
//! Describes a shared memory object management class.

namespace boost {
namespace interprocess {

//! A class that wraps a shared memory mapping that can be used to
//! create mapped regions from the mapped files
class android_shared_memory {
#if !defined(BOOST_INTERPROCESS_DOXYGEN_INVOKED)
  // Non-copyable and non-assignable
  BOOST_MOVABLE_BUT_NOT_COPYABLE(android_shared_memory)
#endif //#ifndef BOOST_INTERPROCESS_DOXYGEN_INVOKED

 public:
  //! Default constructor. Represents an empty android_shared_memory.
  android_shared_memory();

  //! Creates a shared memory object with name "name" and mode "mode", with the access mode "mode"
  //! If the file previously exists, throws an error.*/
  android_shared_memory(create_only_t, const char* name, mode_t mode) {
    this->priv_open_or_create(ipcdetail::DoCreate, name, mode, 1ul);
  }

  //! Tries to create a shared memory object with name "name" and mode "mode", with the
  //! access mode "mode". If the file previously exists, it tries to open it with mode "mode".
  //! Otherwise throws an error.
  android_shared_memory(open_or_create_t, const char* name, mode_t mode) {
    this->priv_open_or_create(ipcdetail::DoOpenOrCreate, name, mode, 1ul);
  }

  //! Tries to open a shared memory object with name "name", with the access mode "mode".
  //! If the file does not previously exist, it throws an error.
  android_shared_memory(open_only_t, const char* name, mode_t mode) {
    this->priv_open_or_create(ipcdetail::DoOpen, name, mode, 1ul);
  }

  //! Creates a shared memory object with name "name" and mode "mode", with the access mode "mode"
  //! If the file previously exists, throws an error.*/
  android_shared_memory(create_only_t, const char* name, mode_t mode, std::size_t size) {
    this->priv_open_or_create(ipcdetail::DoCreate, name, mode, size);
  }

  //! Tries to create a shared memory object with name "name" and mode "mode", with the
  //! access mode "mode". If the file previously exists, it tries to open it with mode "mode".
  //! Otherwise throws an error.
  android_shared_memory(open_or_create_t, const char* name, mode_t mode, std::size_t size) {
    this->priv_open_or_create(ipcdetail::DoOpenOrCreate, name, mode, size);
  }

  //! Tries to open a shared memory object with name "name", with the access mode "mode".
  //! If the file does not previously exist, it throws an error.
  android_shared_memory(open_only_t, const char* name, mode_t mode, std::size_t size) {
    this->priv_open_or_create(ipcdetail::DoOpen, name, mode, size);
  }

  //! Moves the ownership of "moved"'s shared memory object to *this.
  //! After the call, "moved" does not represent any shared memory object.
  //! Does not throw
  android_shared_memory(BOOST_RV_REF(android_shared_memory) moved)
      : m_handle(file_handle_t(ipcdetail::invalid_file())), m_mode(read_only) {
    this->swap(moved);
  }

  //! Moves the ownership of "moved"'s shared memory to *this.
  //! After the call, "moved" does not represent any shared memory.
  //! Does not throw
  android_shared_memory& operator=(BOOST_RV_REF(android_shared_memory) moved) {
    android_shared_memory tmp(boost::move(moved));
    this->swap(tmp);
    return *this;
  }

  //! Swaps the android_shared_memorys. Does not throw
  void swap(android_shared_memory& moved);

  //! Sets the size of the shared memory mapping
  void truncate(offset_t length);

  //! Erases a shared memory object from the system.
  //! Returns false on error. Never throws
  static bool remove(const char* name);

  //! Destroys *this and indicates that the calling process is finished using
  //! the resource. All mapped regions are still
  //! valid after destruction. The destructor function will deallocate
  //! any system resources allocated by the system for use by this process for
  //! this resource. The resource can still be opened again calling
  //! the open constructor overload. To erase the resource from the system
  //! use remove().
  ~android_shared_memory();

  //! Returns the name of the shared memory object.
  const char* get_name() const;

  //! Returns true if the size of the shared memory object
  //! can be obtained and writes the size in the passed reference
  bool get_size(offset_t& size) const;

  //! Returns access mode
  mode_t get_mode() const;

  //! Returns mapping handle. Never throws.
  mapping_handle_t get_mapping_handle() const;

#if !defined(BOOST_INTERPROCESS_DOXYGEN_INVOKED)
 private:
  //! Closes a previously opened file mapping. Never throws.
  void priv_close();

  //! Opens or creates a shared memory object.
  bool priv_open_or_create(
      ipcdetail::create_enum_t type,
      const char* filename,
      mode_t mode,
      std::size_t size);

  file_handle_t m_handle;
  mode_t m_mode;
  std::string m_filename;
#endif //#ifndef BOOST_INTERPROCESS_DOXYGEN_INVOKED
};

#if !defined(BOOST_INTERPROCESS_DOXYGEN_INVOKED)

inline android_shared_memory::android_shared_memory()
    : m_handle(file_handle_t(ipcdetail::invalid_file())), m_mode(read_only) {}

inline android_shared_memory::~android_shared_memory() {
  this->priv_close();
}

inline const char* android_shared_memory::get_name() const {
  return m_filename.c_str();
}

inline bool android_shared_memory::get_size(offset_t& size) const {
  if (m_handle != -1) {
    size = ASharedMemory_getSize(m_handle);
    return true;
  }
  return false;
}

inline void android_shared_memory::swap(android_shared_memory& other) {
  boost::adl_move_swap(m_handle, other.m_handle);
  boost::adl_move_swap(m_mode, other.m_mode);
  m_filename.swap(other.m_filename);
}

inline mapping_handle_t android_shared_memory::get_mapping_handle() const {
  return ipcdetail::mapping_handle_from_file_handle(m_handle);
}

inline mode_t android_shared_memory::get_mode() const {
  return m_mode;
}

namespace android_shared_memory_detail {} // namespace android_shared_memory_detail

inline bool android_shared_memory::priv_open_or_create(
    ipcdetail::create_enum_t type,
    const char* filename,
    mode_t mode,
    std::size_t size) {
  m_filename = filename;

  // Create new mapping
  switch (type) {
    case ipcdetail::DoOpen: {
      // ashmem sections cannot only be opened
      errno = ENOENT;
      m_handle = -1;
    } break;
    case ipcdetail::DoCreate:
    case ipcdetail::DoOpenOrCreate: {
      m_handle = ASharedMemory_create(m_filename.c_str(), size);
    } break;
    default: {
      error_info err = other_error;
      throw interprocess_exception(err);
    }
  }

  // Check for error
  if (m_handle < 0) {
    error_info err = errno;
    this->priv_close();
    throw interprocess_exception(err);
  }

  m_mode = mode;
  return true;
}

inline bool android_shared_memory::remove(const char* filename) {
  return true;
}

inline void android_shared_memory::truncate(offset_t length) {
  const int ret = ioctl(m_handle, ASHMEM_SET_SIZE, length);
  if (ret < 0) {
    error_info err(system_error_code());
    throw interprocess_exception(err);
  }
}

inline void android_shared_memory::priv_close() {
  if (m_handle != -1) {
    ::close(m_handle);
    m_handle = -1;
  }
}

//! A class that stores the name of a shared memory
//! and calls android_shared_memory::remove(name) in its destructor
//! Useful to remove temporary shared memory objects in the presence
//! of exceptions
class remove_shared_memory_on_destroy {
  const char* m_name;

 public:
  remove_shared_memory_on_destroy(const char* name) : m_name(name) {}

  ~remove_shared_memory_on_destroy() {
    android_shared_memory::remove(m_name);
  }
};

#endif //#ifndef BOOST_INTERPROCESS_DOXYGEN_INVOKED

} // namespace interprocess
} // namespace boost

#include <boost/interprocess/detail/config_end.hpp>

#endif // BOOST_INTERPROCESS_ANDROID_SHARED_MEMORY_HPP
