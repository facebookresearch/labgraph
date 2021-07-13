// Copyright 2004-present Facebook. All Rights Reserved.

#pragma once

#include <cthulhu/ForceCleanable.h>
#include <cthulhu/LogDisabling.h>
#include <cthulhu/StreamInterface.h>

namespace cthulhu {

class StreamRegistryInterface : public ForceCleanable, public LogDisabling {
 public:
  virtual ~StreamRegistryInterface() = default;

  // Provides access to the Stream Registry
  // A description is provided. If the stream does not exist, it constructs
  // one in the registry and provides a pointer to it. If the stream exists,
  // a pointer to the existing is returned. This function is thread-safe.
  virtual StreamInterface* registerStream(const StreamDescription& desc) = 0;

  // Provides read-only access to the Stream Registry
  // Returns nullptr if the requested stream does not exist
  virtual StreamInterface* getStream(const StreamID& id) = 0;

  // Other Functionality to expose
  virtual void printStreamInfo() const {}

  // Function for getting all registered StreamID's for a type
  virtual std::vector<StreamID> streamsOfTypeID(uint32_t typeID) const = 0;
};

} // namespace cthulhu
