# LabGraph Protocol

Provides a framework for creating experiment protocols with labgraph

## Quick Start

### Method 1 - building from source code

**Prerequisites**:

Make sure to install labgraph before proceeding

```
cd labgraph/extensions/labgraph_protocol
python setup.py install
```

### Testing:

To make sure things are working you can run any of the following examples

```
python -m extensions.labgraph_protocol.labgraph_protocol.examples PROTOCOL_NAME
```
`PROTOCOL_NAME` can be any of:
- `audio_player`
- `display_image`
- `labels_buttons`
- `random_targets`
- `text_box_w_feedback`
- `video_player`
