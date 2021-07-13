// Copyright 2004-present Facebook. All Rights Reserved.

#pragma once

#include <cthulhu/Framework.h>
#include <cthulhu/StreamType.h>

struct TestSample : public cthulhu::AutoStreamSample {
  using T = TestSample;

  cthulhu::FieldsBegin<T> begin;
  cthulhu::SampleField<uint32_t, T> value{"value", this};
  cthulhu::FieldsEnd<T> end;

  CTHULHU_AUTOSTREAM_SAMPLE(TestSample);
};
