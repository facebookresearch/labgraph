#!/usr/bin/env python3
# Copyright (c) Meta Platforms, Inc. and affiliates.

import labgraph as lg


class ForceTorchATIMessage(lg.TimestampedMessage):
    # The actual shape of this depends on the configuration
    """
    This following fields are the data extracted from the ft sensor.
    The units for force metrics (fx, fy, fz) and torch metrics (tx, ty, tz) can be
    pounds and pound-inches, or, newtons and newton-meters.
    The output units can be configured at the Net F/T Configurations web page.
    fx; // X‑axis force
    fy; // Y‑axis force
    fz; // Z‑axis force
    tx; // X‑axis torque
    ty; // Y‑axis torque
    tz; // Z‑axis torque
    """
    fx: int
    fy: int
    fz: int
    tx: int
    ty: int
    tz: int
