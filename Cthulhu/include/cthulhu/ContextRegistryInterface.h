// Copyright 2004-present Facebook. All Rights Reserved.

#pragma once

#include <cthulhu/ForceCleanable.h>
#include <cthulhu/LogDisabling.h>
#include <cthulhu/StreamInterface.h>

namespace cthulhu {

// ContextInfoInterface provides a handle into data about a specific context
//
// The handle should be used by contexts to update information about their publications and
// subscriptions. Other users will only be given a ConstPtr which can only be used to query
// information about the context, not update it.
class ContextInfoInterface {
 public:
  virtual ~ContextInfoInterface() = default;

  virtual std::string name() const = 0;
  virtual bool isPrivateNamespace() const = 0;

  // Returns some unique identifier for the process that created this context. This value doesn't
  // need to necessarily be a PID, just needs to be guaranteed to be consistent across a process.
  virtual int getPid() const = 0;

  // A context may be marked as invalid if it was e.g. destructed by the owning process. The
  // Registry implementation can choose to keep track of invalid contexts, indicated by this flag.
  virtual bool getValid() const = 0;

  // Each context can register multiple subscribers, publishers, or transformers, and can
  // have multiple streams associated with each call. The output from these 3 methods
  // returns that information as nested vectors, in the order the individual calls
  // (subscribe, advertise, transform) were made.
  using RegistrationGroup = std::vector<StreamID>;
  virtual std::vector<RegistrationGroup> subscriptions() const = 0;
  virtual std::vector<RegistrationGroup> publications() const = 0;
  virtual std::vector<std::pair<RegistrationGroup, RegistrationGroup>> transformations() const = 0;

  virtual void registerSubscriber(const std::vector<StreamID>& streams) = 0;
  virtual void registerPublisher(const std::vector<StreamID>& streams) = 0;
  virtual void registerTransformer(
      const std::vector<StreamID>& inputs,
      const std::vector<StreamID>& outputs) = 0;

  // Convenience overloads since Context uses StreamIDViews all over the place
  virtual void registerSubscriber(const std::vector<StreamIDView>& views) = 0;
  virtual void registerPublisher(const std::vector<StreamIDView>& views) = 0;
  virtual void registerTransformer(
      const std::vector<StreamIDView>& input_views,
      const std::vector<StreamIDView>& output_views) = 0;
};
using ContextInfoInterfaceConstPtr = std::shared_ptr<const ContextInfoInterface>;

class ContextRegistryInterface : public ForceCleanable, public LogDisabling {
 public:
  virtual ~ContextRegistryInterface() = default;

  // Register a new context, and return a handle to it
  //
  // Additional information (subscriber info, etc) should be registered through the
  // returned handle. The caller (context) should not free the returned handle as it is
  // managed by the ContextRegistry.
  virtual ContextInfoInterface* registerContext(std::string_view name, bool private_ns = false) = 0;

  // Remove an existing context from the registry, if it exists
  //
  // Only pointers returned by registerContext() should be passed to removeContext().
  virtual void removeContext(ContextInfoInterface* handle) = 0;

  // Return a vector of handles to all context information
  //
  // This method exists primarily for consumers. Implementations may choose to return a
  // copy of data, or return a const pointer to persistent memory. In the latter case,
  // repeatedly calling methods of ContextInfoInterface will return updated information.
  // However, in either case, to obtain information about new contexts, this method will
  // need to be called again.
  //
  // This method takes a parameter, all, indicating that the Registry implementation should return
  // all contexts it currently knows about. The return value in both cases may be the same, or the
  // contexts returned by setting all=true may be a superset of all=false.
  virtual std::vector<ContextInfoInterfaceConstPtr> contexts(bool all = false) const = 0;
};
} // namespace cthulhu
