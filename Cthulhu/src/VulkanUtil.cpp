// Copyright 2004-present Facebook. All Rights Reserved.

#include <cthulhu/VulkanUtil.h>

#ifdef _WIN32
#include <windows.h>
#else
#include <unistd.h>
#endif

#ifdef CTHULHU_HAS_VULKAN
#include <vulkan/vulkan.h>
#endif

#include <cstdlib>

#define DEFAULT_LOG_CHANNEL "Cthulhu"
#include <logging/Log.h>

#ifdef CTHULHU_HAS_VULKAN
// Load the functions from the external memory extensions
#ifdef _WIN32
VkResult vkGetMemoryWin32HandleKHR(
    VkDevice device,
    const VkMemoryGetWin32HandleInfoKHR* pInfo,
    HANDLE* pHandle) {
  auto vkGetMemoryWin32HandleKHR2 =
      PFN_vkGetMemoryWin32HandleKHR(vkGetDeviceProcAddr(device, "vkGetMemoryWin32HandleKHR"));
  return vkGetMemoryWin32HandleKHR2(device, pInfo, pHandle);
}
#else
VkResult vkGetMemoryFdKHR(VkDevice device, const VkMemoryGetFdInfoKHR* pInfo, int* pFd) {
  auto vkGetMemoryFdKHR2 = PFN_vkGetMemoryFdKHR(vkGetDeviceProcAddr(device, "vkGetMemoryFdKHR"));
  return vkGetMemoryFdKHR2(device, pInfo, pFd);
}
#endif // _WIN32
#endif // CTHULHU_HAS_VULKAN

namespace cthulhu {

#ifdef CTHULHU_HAS_VULKAN
struct VulkanUtilState {
  VkInstance instance = VK_NULL_HANDLE;
  VkPhysicalDevice physicalDevice = VK_NULL_HANDLE;
  VkDevice device = VK_NULL_HANDLE;
  VkPhysicalDeviceMemoryProperties memoryProperties;
};

uint32_t findMemoryTypeIndex(
    const VkPhysicalDeviceMemoryProperties& memoryProperties,
    uint32_t memoryTypeBits,
    VkFlags required,
    VkFlags preferred,
    VkFlags preferredNot) {
  // first try, find required and with preferred and without preferred_not
  for (uint32_t i = 0; i < memoryProperties.memoryTypeCount; i++) {
    bool isSupported = (1 << i) & memoryTypeBits;
    if (isSupported) {
      const VkMemoryType& memoryType = memoryProperties.memoryTypes[i];
      if ((memoryType.propertyFlags & required) == required &&
          (preferred && (memoryType.propertyFlags & preferred)) &&
          (preferredNot && !(memoryType.propertyFlags & preferredNot))) {
        return i;
      }
    }
  }

  // second try, find required and with preferred
  for (uint32_t i = 0; i < memoryProperties.memoryTypeCount; i++) {
    bool isSupported = (1 << i) & memoryTypeBits;
    if (isSupported) {
      const VkMemoryType& memoryType = memoryProperties.memoryTypes[i];
      if ((memoryType.propertyFlags & required) == required &&
          (preferred && (memoryType.propertyFlags & preferred))) {
        return i;
      }
    }
  }

  // third try, find required and without preferred_not
  for (uint32_t i = 0; i < memoryProperties.memoryTypeCount; i++) {
    bool isSupported = (1 << i) & memoryTypeBits;
    if (isSupported) {
      const VkMemoryType& memoryType = memoryProperties.memoryTypes[i];
      if ((memoryType.propertyFlags & required) == required &&
          (preferredNot && !(memoryType.propertyFlags & preferredNot))) {
        return i;
      }
    }
  }

  // fourth try, find any required
  for (uint32_t i = 0; i < memoryProperties.memoryTypeCount; i++) {
    bool isSupported = (1 << i) & memoryTypeBits;
    if (isSupported) {
      const VkMemoryType& memoryType = memoryProperties.memoryTypes[i];
      if ((memoryType.propertyFlags & required) == required) {
        return i;
      }
    }
  }

  XR_LOGE("No such memory type {} {} {} {}", memoryTypeBits, required, preferred, preferredNot);
  return -1;
}
#else
// We forward declared this, so it needs to be provided to make clang happy
struct VulkanUtilState {
  bool dummy;
};
#endif // CTHULHU_HAS_VULKAN

VulkanUtil::VulkanUtil() {
#ifdef CTHULHU_HAS_VULKAN
  if (std::getenv("CTHULHU_DISABLE_VULKAN")) {
    return;
  }

  state_ = new VulkanUtilState();

  // dummy app info
  VkApplicationInfo applicationInfo = {};
  applicationInfo.sType = VK_STRUCTURE_TYPE_APPLICATION_INFO;
  applicationInfo.pApplicationName = "Cthulhu";
  applicationInfo.applicationVersion = 0;
  applicationInfo.pEngineName = "Cthulhu";
  applicationInfo.engineVersion = 0;
  applicationInfo.apiVersion = VK_API_VERSION_1_0;
  VkInstanceCreateInfo createInfo = {};
  createInfo.sType = VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO;
  createInfo.flags = 0;
  createInfo.pApplicationInfo = &applicationInfo;

  // enable debug info
  std::vector<const char*> enabledExtensions{
      VK_KHR_EXTERNAL_MEMORY_CAPABILITIES_EXTENSION_NAME,
      VK_KHR_EXTERNAL_SEMAPHORE_CAPABILITIES_EXTENSION_NAME};
  createInfo.enabledExtensionCount = enabledExtensions.size();
  createInfo.ppEnabledExtensionNames = enabledExtensions.data();
  std::vector<const char*> layers = {
#ifdef _DEBUG
      "VK_LAYER_LUNARG_standard_validation"
#endif
  };
  createInfo.enabledLayerCount = layers.size();
  createInfo.ppEnabledLayerNames = layers.data();
  createInfo.pNext = nullptr;

  if (vkCreateInstance(&createInfo, nullptr, &state_->instance) != VK_SUCCESS) {
    XR_LOGW("Failed to create Vulkan instance!");
    return;
  }

  uint32_t numDevices;
  vkEnumeratePhysicalDevices(state_->instance, &numDevices, nullptr);
  if (!numDevices) {
    XR_LOGW("No Vulkan devices found!");
    return;
  }
  std::vector<VkPhysicalDevice> devices(numDevices);
  vkEnumeratePhysicalDevices(state_->instance, &numDevices, devices.data());

  // Select the requested device
  long int deviceIdx = 0;
  auto deviceIdxStr = std::getenv("CTHULHU_GPU_DEVICE_IDX");
  if (deviceIdxStr) {
    char* pEnd;
    deviceIdx = std::strtol(deviceIdxStr, &pEnd, 10);
    if (pEnd == deviceIdxStr) {
      XR_LOGW(
          "Detected malformed CTHULHU_GPU_DEVICE_IDX: [{}]. Defaulting to device 0.", deviceIdxStr);
    }
    if (deviceIdx >= devices.size()) {
      XR_LOGW(
          "Requested invalid CTHULHU_GPU_DEVICE_IDX: [{}]. [{}] devices are available. Defaulting to device 0.",
          deviceIdx,
          devices.size());
      deviceIdx = 0;
    }
  }
  state_->physicalDevice = devices[deviceIdx];

  // Retain the physical device's memory properties for use
  vkGetPhysicalDeviceMemoryProperties(state_->physicalDevice, &state_->memoryProperties);

  // Request a queue, just because Vulkan requires it.
  VkDeviceQueueCreateInfo deviceQueueCreateInfo;
  deviceQueueCreateInfo.sType = VK_STRUCTURE_TYPE_DEVICE_QUEUE_CREATE_INFO;
  deviceQueueCreateInfo.pNext = 0;
  deviceQueueCreateInfo.flags = 0;
  deviceQueueCreateInfo.queueFamilyIndex = 0;
  deviceQueueCreateInfo.queueCount = 1;
  deviceQueueCreateInfo.pQueuePriorities = nullptr;

  VkDeviceCreateInfo deviceCreateInfo = {};

  std::vector<const char*> enabledExtensions2 = {
      VK_KHR_EXTERNAL_MEMORY_EXTENSION_NAME,
      VK_KHR_EXTERNAL_SEMAPHORE_EXTENSION_NAME,
#ifdef _WIN32
      VK_KHR_EXTERNAL_MEMORY_WIN32_EXTENSION_NAME,
      VK_KHR_EXTERNAL_SEMAPHORE_WIN32_EXTENSION_NAME,
#else
      VK_KHR_EXTERNAL_MEMORY_FD_EXTENSION_NAME,
      VK_KHR_EXTERNAL_SEMAPHORE_FD_EXTENSION_NAME,
#endif
  };
  deviceCreateInfo.sType = VK_STRUCTURE_TYPE_DEVICE_CREATE_INFO;
  deviceCreateInfo.enabledExtensionCount = enabledExtensions2.size();
  deviceCreateInfo.ppEnabledExtensionNames = enabledExtensions2.data();
  deviceCreateInfo.queueCreateInfoCount = 1;
  deviceCreateInfo.pQueueCreateInfos = &deviceQueueCreateInfo;

  if (vkCreateDevice(state_->physicalDevice, &deviceCreateInfo, nullptr, &state_->device) !=
      VK_SUCCESS) {
    XR_LOGW("Failed to create Vulkan logical device!");
    return;
  }

  isActive_ = true;
#else
  (void)state_;
#endif // CTHULHU_HAS_VULKAN
}

VulkanUtil::~VulkanUtil() {
#ifdef CTHULHU_HAS_VULKAN
  if (state_ && state_->device != VK_NULL_HANDLE) {
    vkDestroyDevice(state_->device, nullptr);
  }

  if (state_ && state_->instance != VK_NULL_HANDLE) {
    vkDestroyInstance(state_->instance, nullptr);
  }

  if (state_) {
    delete state_;
  }
#endif
}

std::pair<uint64_t, uint32_t> VulkanUtil::allocate(uint32_t nrBytes, bool deviceLocal) {
#ifdef CTHULHU_HAS_VULKAN
  if (!isActive_) {
    return {0, 0};
  }

  // Create a buffer, just to get memory requirements
  VkBufferCreateInfo bufferCreateInfo = {VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO};
  bufferCreateInfo.size = nrBytes;
  bufferCreateInfo.usage = VK_BUFFER_USAGE_STORAGE_BUFFER_BIT;

  // Enable export
  VkExternalMemoryBufferCreateInfo infoEx{VK_STRUCTURE_TYPE_EXTERNAL_MEMORY_BUFFER_CREATE_INFO};
#ifdef _WIN32
  infoEx.handleTypes = VK_EXTERNAL_MEMORY_HANDLE_TYPE_OPAQUE_WIN32_BIT;
#else
  infoEx.handleTypes = VK_EXTERNAL_MEMORY_HANDLE_TYPE_OPAQUE_FD_BIT;
#endif
  bufferCreateInfo.pNext = &infoEx;

  VkBuffer buffer;
  if (vkCreateBuffer(state_->device, &bufferCreateInfo, nullptr, &buffer) != VK_SUCCESS) {
    XR_LOGW("Failed to allocate Vulkan buffer");
    return {0, 0};
  }

  // Require host visible, coherent memory
  VkMemoryRequirements memReqs;
  vkGetBufferMemoryRequirements(state_->device, buffer, &memReqs);
  VkExportMemoryAllocateInfoKHR vulkanExportMemoryAllocateInfoKHR = {};
  vulkanExportMemoryAllocateInfoKHR.sType = VK_STRUCTURE_TYPE_EXPORT_MEMORY_ALLOCATE_INFO_KHR;
  vulkanExportMemoryAllocateInfoKHR.pNext = nullptr;
#ifdef _WIN32
  vulkanExportMemoryAllocateInfoKHR.handleTypes = VK_EXTERNAL_MEMORY_HANDLE_TYPE_OPAQUE_WIN32_BIT;
#else
  vulkanExportMemoryAllocateInfoKHR.handleTypes = VK_EXTERNAL_MEMORY_HANDLE_TYPE_OPAQUE_FD_BIT;
#endif

  VkMemoryAllocateInfo allocateInfo = {};
  allocateInfo.sType = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO;
  allocateInfo.pNext = &vulkanExportMemoryAllocateInfoKHR;
  allocateInfo.allocationSize = memReqs.size;
  VkFlags required, preferred, preferredNot;
  if (deviceLocal) {
    required = VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT;
    preferred = 0;
    preferredNot = 0;
  } else {
    required = VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT | VK_MEMORY_PROPERTY_HOST_COHERENT_BIT;
    preferred = VK_MEMORY_PROPERTY_HOST_CACHED_BIT;
    preferredNot = VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT;
  }
  allocateInfo.memoryTypeIndex = findMemoryTypeIndex(
      state_->memoryProperties, memReqs.memoryTypeBits, required, preferred, preferredNot);

  // Allocate the memory
  VkDeviceMemory bufferMemory;
  if (vkAllocateMemory(state_->device, &allocateInfo, nullptr, &bufferMemory) != VK_SUCCESS) {
    XR_LOGW("Failed to allocate Vulkan buffer memory!");
    return {0, 0};
  }

  // We no longer need the buffer
  vkDestroyBuffer(state_->device, buffer, nullptr);

#ifdef _WIN32
  VkMemoryGetWin32HandleInfoKHR info = {VK_STRUCTURE_TYPE_MEMORY_GET_WIN32_HANDLE_INFO_KHR};
  HANDLE handle{};
  info.handleType = VK_EXTERNAL_MEMORY_HANDLE_TYPE_OPAQUE_WIN32_BIT;
  info.memory = bufferMemory;
  vkGetMemoryWin32HandleKHR(state_->device, &info, &handle);
#else
  VkMemoryGetFdInfoKHR info = {VK_STRUCTURE_TYPE_MEMORY_GET_FD_INFO_KHR};
  int handle{};
  info.handleType = VK_EXTERNAL_MEMORY_HANDLE_TYPE_OPAQUE_FD_BIT;
  info.memory = bufferMemory;
  vkGetMemoryFdKHR(state_->device, &info, &handle);
#endif

  return {(uint64_t)handle, allocateInfo.memoryTypeIndex};
#endif // CTHULHU_HAS_VULKAN
  XR_LOGW("Failed to allocate GPU buffer. Vulkan support was not included in build.");
  return {0, 0};
}

void VulkanUtil::free(uint64_t handle) {
#ifdef CTHULHU_HAS_VULKAN
#ifdef _WIN32
  CloseHandle((HANDLE)handle);
#else
  close((int)handle);
#endif // _WIN32
#endif // CTHULHU_HAS_VULKAN
}

std::shared_ptr<uint8_t>
VulkanUtil::map(uint64_t handle, uint32_t nrBytes, uint32_t memoryTypeIndex) {
#ifdef CTHULHU_HAS_VULKAN
  if (!isActive_) {
    return nullptr;
  }

  // Re-import the handle into memory
#ifdef _WIN32
  VkImportMemoryWin32HandleInfoKHR vulkanImportMemoryHandleInfo = {};
  vulkanImportMemoryHandleInfo.sType = VK_STRUCTURE_TYPE_IMPORT_MEMORY_WIN32_HANDLE_INFO_KHR;
  vulkanImportMemoryHandleInfo.handleType = VK_EXTERNAL_MEMORY_HANDLE_TYPE_OPAQUE_WIN32_BIT;
  vulkanImportMemoryHandleInfo.handle = (HANDLE)handle;
#else
  VkImportMemoryFdInfoKHR vulkanImportMemoryHandleInfo = {};
  vulkanImportMemoryHandleInfo.sType = VK_STRUCTURE_TYPE_IMPORT_MEMORY_FD_INFO_KHR;
  vulkanImportMemoryHandleInfo.handleType = VK_EXTERNAL_MEMORY_HANDLE_TYPE_OPAQUE_FD_BIT;
  vulkanImportMemoryHandleInfo.fd = dup((int)handle);
#endif

  VkMemoryAllocateInfo allocateInfo = {};
  allocateInfo.sType = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO;
  allocateInfo.pNext = &vulkanImportMemoryHandleInfo;
  allocateInfo.allocationSize = nrBytes;
  allocateInfo.memoryTypeIndex = memoryTypeIndex;

  // "Allocate" the memory, but really just import it
  VkDeviceMemory bufferMemory;
  auto ret = vkAllocateMemory(state_->device, &allocateInfo, nullptr, &bufferMemory);
  if (ret != VK_SUCCESS) {
    XR_LOGW(
        "Failed to import Vulkan buffer memory at handle {}! Size {}, memory type {}. Error code was {}.",
        handle,
        nrBytes,
        memoryTypeIndex,
        ret);
    return nullptr;
  }

  // Map it to the host
  void* result = nullptr;
  if (vkMapMemory(state_->device, bufferMemory, 0, nrBytes, 0, &result) != VK_SUCCESS) {
    XR_LOGW("Failed to map Vulkan buffer to host memory.");
    return nullptr;
  }

  return std::shared_ptr<uint8_t>((uint8_t*)result, [this, bufferMemory](uint8_t* ptr) -> void {
    vkFreeMemory(state_->device, bufferMemory, nullptr);
  });
#endif // CTHULHU_HAS_VULKAN
  XR_LOGW("Failed to map GPU buffer. Vulkan support was not included in build.");
  return nullptr;
}

bool VulkanUtil::isActive() const {
  return isActive_;
}

bool VulkanUtil::isDeviceLocal(uint32_t memoryTypeIndex) const {
#ifdef CTHULHU_HAS_VULKAN
  if (memoryTypeIndex > state_->memoryProperties.memoryTypeCount) {
    throw std::runtime_error("memoryTypeIndex out of range");
  }
  return state_->memoryProperties.memoryTypes[memoryTypeIndex].propertyFlags &
      VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT;
#else
  return false;
#endif
}

} // namespace cthulhu
