
# LabGraph Vision Object Detection Android Demo

### Overview

This is an object detection app that continuously detects the objects (bounding boxes, classes, and confidence) in the frames of a video imported by the device gallery, with the option to use a quantized [MobileNetV2](https://storage.cloud.google.com/tf_model_garden/vision/qat/mobilenetv2_ssd_coco/mobilenetv2_ssd_256_uint8.tflite) [EfficientDet Lite 0](https://storage.googleapis.com/mediapipe-tasks/object_detector/efficientdet_lite0_uint8.tflite), or [EfficientDet Lite2](https://storage.googleapis.com/mediapipe-tasks/object_detector/efficientdet_lite2_uint8.tflite) model.

The model files are downloaded by a Gradle script when you build and run the app. You don't need to do any steps to download TFLite models into the project explicitly unless you wish to use your own models. If you do use your own models, place them into the app's *assets* directory.

This application should be run on a physical Android device to take advantage of the gallery, though it will enable you to use an emulator for opening locally stored files.

## Build the demo using Android Studio

### Prerequisites

*   The **[Android Studio](https://developer.android.com/studio/index.html)**
    IDE. This sample has been tested on Android Studio Flamingo.

*   A physical Android device with a minimum OS version of SDK 24 (Android 7.0 -
    Nougat) with developer mode enabled. The process of enabling developer mode
    may vary by device. You may also use an Android emulator with more limited
    functionality.

### Building

*   Open Android Studio. From the Welcome screen, select Open an existing
    Android Studio project.

*   From the Open File or Project window that appears, navigate to and select
    the labgraph/android/vision directory. Click OK. You may
    be asked if you trust the project. Select Trust.

*   If it asks you to do a Gradle Sync, click OK.

*   With your Android device connected to your computer and developer mode
    enabled, click on the green Run arrow in Android Studio.

### Models used

Downloading, extraction, and placing the models into the *assets* folder is
managed automatically by the **download.gradle** file.

### Results

The results of the detection are logged into the LogCat console under the "Result" field.
