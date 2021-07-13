// Copyright 2004-present Facebook. All Rights Reserved.

#pragma once

#include <cthulhu/ContextRegistryInterface.h>

namespace cthulhu {

class ContextInfoLocal : public ContextInfoInterface {
 public:
  virtual ~ContextInfoLocal() = default;

  ContextInfoLocal(std::string_view name, bool private_ns) : name_(name), private_ns_(private_ns) {}

  inline std::string name() const override {
    return name_;
  }

  inline bool isPrivateNamespace() const override {
    return private_ns_;
  }

  inline int getPid() const override {
    // This is local, so we don't have any IPC to worry about, and thus PID of 0 is fine.
    return 0;
  }

  inline bool getValid() const override {
    // We remove contexts when they're destructed, so any contexts that can call this method are
    // necessarily valid.
    return true;
  }

  inline std::vector<RegistrationGroup> subscriptions() const override {
    return subscriptions_;
  }

  inline std::vector<RegistrationGroup> publications() const override {
    return publications_;
  }

  inline std::vector<std::pair<RegistrationGroup, RegistrationGroup>> transformations()
      const override {
    return transformations_;
  }

  inline void registerSubscriber(const std::vector<StreamID>& streams) override {
    subscriptions_.emplace_back(streams);
  }

  inline void registerPublisher(const std::vector<StreamID>& streams) override {
    publications_.emplace_back(streams);
  }

  inline void registerTransformer(
      const std::vector<StreamID>& inputs,
      const std::vector<StreamID>& outputs) override {
    transformations_.emplace_back(inputs, outputs);
  }

  inline void registerSubscriber(const std::vector<StreamIDView>& views) override {
    // Copy from each of the views into a new StreamID
    auto& streams = subscriptions_.emplace_back();
    streams.reserve(views.size());
    for (const auto& view : views) {
      streams.emplace_back(view);
    }
  }

  inline void registerPublisher(const std::vector<StreamIDView>& views) override {
    // Copy from each of the views into a new StreamID
    auto& streams = publications_.emplace_back();
    streams.reserve(views.size());
    for (const auto& view : views) {
      streams.emplace_back(view);
    }
  }

  inline virtual void registerTransformer(
      const std::vector<StreamIDView>& input_views,
      const std::vector<StreamIDView>& output_views) override {
    auto& [inputs, outputs] = transformations_.emplace_back();

    inputs.reserve(input_views.size());
    for (const auto& view : input_views) {
      inputs.emplace_back(view);
    }

    outputs.reserve(output_views.size());
    for (const auto& view : output_views) {
      outputs.emplace_back(view);
    }
  }

 private:
  std::string name_;
  bool private_ns_;
  std::vector<ContextInfoInterface::RegistrationGroup> subscriptions_;
  std::vector<ContextInfoInterface::RegistrationGroup> publications_;
  std::vector<
      std::pair<ContextInfoInterface::RegistrationGroup, ContextInfoInterface::RegistrationGroup>>
      transformations_;
};

class ContextRegistryLocal : public ContextRegistryInterface {
 public:
  virtual ~ContextRegistryLocal() = default;

  ContextInfoInterface* registerContext(std::string_view name, bool private_ns = false) override;
  void removeContext(ContextInfoInterface* handle) override;
  std::vector<ContextInfoInterfaceConstPtr> contexts(bool all = false) const override;

 private:
  std::vector<std::shared_ptr<ContextInfoLocal>> contexts_;
};

} // namespace cthulhu
