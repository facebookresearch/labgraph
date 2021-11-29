#include "SubAlignerImpl.h"

#include <algorithm>

namespace cthulhu {

namespace subaligner {

StreamInterface::StreamInterface(Aligner* aligner, int identifier)
    : aligner_(aligner), identifier_(identifier) {
  assert(aligner_ != nullptr);
}

int StreamInterface::index() const {
  return identifier_;
}

void StreamInterface::release() {
  aligner_->release(identifier_);
}

void StreamInterface::primarize() {
  aligner_->primarize(identifier_);
}

bool StreamInterface::isPrimary() {
  return aligner_->isPrimary(identifier_);
}

double StreamInterface::obtainSamplePeriod(int multiplier) const {
  return aligner_->obtainSamplePeriod(identifier_, multiplier);
}

void StreamInterface::feed(
    const Buffer& buf,
    size_t buf_size,
    double start_time,
    double end_time,
    double surrogate_timestamp) {
  aligner_->enqueue(identifier_, buf, buf_size, start_time, end_time, surrogate_timestamp);
}

Statistics StreamInterface::getStats() const {
  return aligner_->getStats(identifier_);
}

// struct Aligner::Metronome
// =========================
// Public Methods

void Aligner::Metronome::propagate(BufferDurationalTagged& batch) {
  if (previous_batch.buffer_durational.duration.end_time <
      previous_batch.buffer_durational.duration.start_time) {
    previous_batch.buffer_durational.duration.end_time =
        batch.buffer_durational.duration.start_time;
    previous_batch.sample_rate = static_cast<double>(previous_batch.nrsamples_total) /
        (previous_batch.buffer_durational.duration.end_time -
         previous_batch.buffer_durational.duration.start_time);
  }

  if (previous_batch.sample_rate > 0)
    update(previous_batch);
  else
    reference_time_estimate.decimal = batch.buffer_durational.duration.start_time;

  previous_batch.buffer_durational.duration = batch.buffer_durational.duration;
  previous_batch.nrsamples_total = batch.nrsamples_total;
  previous_batch.sample_rate = batch.sample_rate;

  batch.sample_rate = sample_rate_estimate.decimal;
  batch.buffer_durational.duration.start_time =
      nrsamples_cumulative / sample_rate_estimate.decimal + reference_time_estimate.decimal;
  batch.buffer_durational.duration.end_time = batch.buffer_durational.duration.start_time +
      batch.nrsamples_total / sample_rate_estimate.decimal;
}

double Aligner::Metronome::obtainSampleRateEstimate() const {
  return sample_rate_estimate.decimal;
}

void Aligner::Metronome::reset() {
  // The sample rate estimate is slightly regulated to be closer to the nominal rate.
  sample_rate_estimate.numerator = 1;
  sample_rate_estimate.denominator = nominal_rate;
  sample_rate_estimate.decimal = nominal_rate;

  // Some of the fields that will be used for updates need to be initialized.
  previous_batch.buffer_durational.duration.start_time = 0;
  previous_batch.buffer_durational.duration.end_time = 1;
  previous_batch.sample_rate = -1;

  reference_time_estimate = Fraction();
  nrsamples_cumulative = 0;
}

Aligner::Metronome::Metronome(size_t _sample_bytewidth, double _nominal_rate)
    : sample_bytewidth(_sample_bytewidth), nominal_rate(_nominal_rate) {
  reset();
}

// struct Aligner::Metronome
// =========================
// Protected Methods

void Aligner::Metronome::update(const BufferDurationalTagged& batch) {
  // Update the estimation of the reference time. This time is what all refined timestamps
  // would be referencing to - whereas using the timestamp of the first batch would lead to
  // systematic bias if the first timestamp is biased.

  reference_time_estimate.denominator += 1;
  reference_time_estimate.numerator +=
      (batch.buffer_durational.duration.start_time + batch.buffer_durational.duration.end_time -
       batch.nrsamples_total / sample_rate_estimate.decimal) /
          2.0 -
      nrsamples_cumulative / sample_rate_estimate.decimal;
  reference_time_estimate.decimal =
      reference_time_estimate.numerator / reference_time_estimate.denominator;

  // Update the estimateion for the sample rate. The sample rate and time reference are solutions
  // to a least-squares optimization problem based on the history of start times and number of
  // samples, by essentially fitting them onto a line. Those two variables in question are the
  // slope and intercept respectively.

  sample_rate_estimate.denominator +=
      2.0 * nrsamples_cumulative * (nrsamples_cumulative + batch.nrsamples_total) +
      batch.nrsamples_total * batch.nrsamples_total;
  sample_rate_estimate.numerator += nrsamples_cumulative *
          (batch.buffer_durational.duration.start_time + batch.buffer_durational.duration.end_time -
           2.0 * reference_time_estimate.decimal) +
      batch.nrsamples_total *
          (batch.buffer_durational.duration.end_time - reference_time_estimate.decimal);
  sample_rate_estimate.decimal = sample_rate_estimate.denominator / sample_rate_estimate.numerator;

  nrsamples_cumulative += batch.nrsamples_total;
}

StreamInterface* Aligner::enroll(size_t sample_bytewidth, double timestamp_offset) {
  Stream stream;
  stream.nrbytes_pending = 0;
  stream.nrsamples_processed = 0;
  stream.manifest_upstream_index = 0;
  stream.deficit = 0.0;
  stream.identifier = static_cast<int>(registry_.size());
  stream.sample_bytewidth = sample_bytewidth;
  stream.timestamp_offset = timestamp_offset;

  auto identifier = stream.identifier;
  registry_[identifier] = new Stream(stream);
  stream_interfaces_.emplace(identifier, new StreamInterface(this, identifier));
  return stream_interfaces_[identifier];
}

StreamInterface*
Aligner::enroll(size_t sample_bytewidth, double nominal_rate, double timestamp_offset) {
  auto feeder = enroll(sample_bytewidth, timestamp_offset);
  if (nominal_rate > 0.0) {
    registry_[feeder->identifier_]->metronome = // install a metronome for fixed-rate data stream.
        std::make_shared<Aligner::Metronome>(sample_bytewidth, nominal_rate);
  }

  return feeder;
}

void Aligner::primarize(int identifier) {
  primary_stream_id = identifier;
}

bool Aligner::isPrimary(int identifier) const {
  return (primary_stream_id == identifier);
}

void Aligner::release(int identifier) {
  registry_.erase(identifier);
  stream_interfaces_.erase(identifier);
}

double Aligner::obtainSamplePeriod(int identifier, int multiplier) const {
  double sample_rate = -1.0;

  auto it = registry_.find(identifier);
  if (it != registry_.cend()) {
    auto& stream = it->second;
    if (stream->metronome)
      sample_rate = stream->metronome->obtainSampleRateEstimate();
    else if (!stream->batches.empty())
      sample_rate = stream->batches.front().sample_rate;
  }

  // Implicit upcast to double.
  return multiplier / sample_rate;
}

Statistics Aligner::getStats(int identifier) const {
  auto it = registry_.find(identifier);
  if (it != registry_.cend())
    return it->second->stats;
  else
    return Statistics();
}

void Aligner::enqueue(
    int identifier,
    const Buffer& buf,
    size_t buf_size,
    double start_time,
    double end_time,
    double surrogate_timestamp) {
  auto& stream = *registry_[identifier]; // This cannot possibly fail.

  BufferDurationalTagged batch;
  batch.sequence_number = stream.stats.batches_received;
  batch.nrsamples_total = buf_size / stream.sample_bytewidth;
  batch.nrsamples_current = 0;
  batch.sample_rate = 1.0;
  batch.duration_unadjusted.start_time = start_time + stream.timestamp_offset;
  batch.duration_unadjusted.end_time = end_time + stream.timestamp_offset;
  batch.buffer_durational.buffer = buf;
  batch.buffer_durational.duration = batch.duration_unadjusted;
  assert(batch.nrsamples_total * stream.sample_bytewidth == buf_size);

  stream.stats.batches_received += 1;
  stream.stats.samples_received += batch.nrsamples_total;

  // There are two possibilities on the end_time: if it is less than the start time,
  // the invoker chooses not to provide a valid lifespan for this batch, in which case
  // the determintion of the end time is deferred until the receipt of the next batch,
  // the start time of which will be used as the end time here; or, if it is equal to or
  // greater than the start time, the lifespan is valid and should be used immediately.
  // The metronome regulates the start and end times in either cases.

  std::vector<Duration*> duration_requests;
  auto finalizeBatch = [&](BufferDurationalTagged& batch) {
    duration_requests.push_back(&batch.buffer_durational.duration);
    batch.sample_rate = static_cast<double>(batch.nrsamples_total) /
        (batch.buffer_durational.duration.end_time - batch.buffer_durational.duration.start_time);
  };

  if (stream.metronome)
    stream.metronome->propagate(batch); // This potentially ratifies the batch's linespan.
  if (batch.buffer_durational.duration.end_time > batch.buffer_durational.duration.start_time)
    finalizeBatch(batch);
  if (!stream.batches.empty()) {
    auto& previous_batch = stream.batches.back();
    if (previous_batch.buffer_durational.duration.end_time <
        previous_batch.buffer_durational.duration.start_time) {
      previous_batch.buffer_durational.duration.end_time =
          batch.buffer_durational.duration.start_time;
      finalizeBatch(
          previous_batch); // Populate the duration requests and calculate the sample rate.
    }
  }

  // If the identifier is not equal to the primary stream identifier, we would not
  // need to put into the requests for manifests. In that case, the list of potential
  // duration requests are cleared.

  if (identifier != primary_stream_id) {
    duration_requests.clear();
  }

  std::for_each(duration_requests.begin(), duration_requests.end(), [&](Duration* duration) {
    request(duration->start_time, duration->end_time);
  });

  stream.batches.push_back(std::move(batch));
  return;
}

void Aligner::request(double start_time, double end_time) {
  Manifest manifest;
  manifest.duration.start_time = start_time;
  manifest.duration.end_time = end_time;
  for (auto& stream : registry_)
    stream.second->deficit += start_time - end_time;

  active_manifests_.push_back(std::move(manifest));
  return;
}

int Aligner::finalizeOne() {
  if (!active_manifests_.empty()) {
    auto& manifest = active_manifests_.front();

    // This statement implements the following semantics: if the user decides to forcefully
    // finalize one manifest, samples that arrive after that point will not be retrospectively
    // considered for alignment in that finalized manifest anymore; instead, they will be
    // only considered for the subsequent manifest requests.

    for (auto& stream : registry_)
      stream.second->manifest_upstream_index =
          std::max(stream.second->manifest_upstream_index - 1, 0);

    // If there is an active manifest, we finalize it by passing it to the completed
    // manifest queue for shipment, regardless of its completion status. Stats are also updated.

    for (const auto& pair : manifest.references) {
      auto& stream = *registry_[pair.first];
      stream.stats.batches_emitted++;
      stream.stats.samples_emitted += stream.nrsamples_processed;
      stream.nrbytes_pending -= stream.nrsamples_processed * stream.sample_bytewidth;
      stream.nrsamples_processed = 0;
    }

    completed_manifests_.push_back(std::move(manifest));
    active_manifests_.pop_front();
    return 1;
  }

  return 0;
}

int Aligner::finalize(int nr_manifests) {
  int nr_finalized = 0;
  while (nr_finalized < nr_manifests && finalizeOne() > 0)
    nr_finalized++;

  return nr_finalized;
}

int Aligner::finalizeBefore(double time_point) {
  int nr_finalized = 0;
  while (!active_manifests_.empty()) {
    auto& manifest = active_manifests_.front();
    if (manifest.duration.end_time < time_point)
      nr_finalized += finalizeOne();
    else
      break;
  }

  return nr_finalized;
}

void Aligner::flush() {
  nr_manifests_emitted = 0;
  nr_manifests_completed = 0;
  active_manifests_.clear();
  completed_manifests_.clear();
  for (auto& item : registry_) {
    auto& stream = item.second;
    if (stream->metronome)
      stream->metronome->reset();

    stream->stats = {};
    stream->nrbytes_pending = 0;
    stream->nrsamples_processed = 0;
    stream->manifest_upstream_index = 0;
    stream->deficit = 0;
    stream->batches.clear();
  }
}

int Aligner::align(int identifier_hint) {
  bool should_switch = false; // Should switch to another stream?

  // A non-negative identifier hint means that a batch of samples from the corresponding stream
  // has been received, and we should examine the possiblity for alignment of all manifests for
  // that stream.
  std::vector<int> relevant_streams;
  if (identifier_hint >= 0)
    relevant_streams.push_back(identifier_hint);
  else {
    // If the hint is negative, examine all the streams.
    relevant_streams.resize(registry_.size());
    std::iota(relevant_streams.begin(), relevant_streams.end(), 0);
  }

  for (const auto& identifier : relevant_streams) {
    should_switch = false;
    auto& stream = *registry_[identifier];

    // Attempt for alignment if there are active manifests and batches. Continue until
    // either all manifests are complete of this stream or there are no batches anymore.

    while (!should_switch && stream.manifest_upstream_index < active_manifests_.size()) {
      auto& manifest = active_manifests_[stream.manifest_upstream_index];
      should_switch = stream.batches.empty();
      // Cannot proceed if we don't have batches for alignment business.

      while (!should_switch && !stream.batches.empty()) {
        auto& batch = stream.batches.front();
        if (batch.buffer_durational.duration.end_time <
            batch.buffer_durational.duration.start_time) {
          should_switch = true;
          break; // Cannot proceed if the batch doesn't have an end time.
        }

        // The manifest proposes the new offset in units of samples within the active batch to be
        // this much... 0.5 is added to enforce the fifth assumption - see above and consider that
        // double -> size_t is truncation.
        auto proposed_sampleoffset = static_cast<int64_t>(
            batch.sample_rate *
                (manifest.duration.end_time - batch.buffer_durational.duration.start_time) +
            0.5);
        if (proposed_sampleoffset <= static_cast<int64_t>(batch.nrsamples_current)) {
          // This means that the request does not require samples beyond the current pointer
          // within the batch. Consider the manifest to be complete of this stream in this case.

          manifest.completed_streams.insert(identifier);
          stream.manifest_upstream_index++; // Proceed to the next manifest.
          if (manifest.completed_streams.size() == registry_.size())
            nr_manifests_completed += finalizeOne();

          // Break to obtain reference to the new manifest.
          break;
        } else {
          // nr_samples can only be zero if and and only if batch.nrsamples_total =
          // batch.nrsamples_current, in which case this batch should be dropped. If it is
          // non-zero, insert a reference to the container.
          size_t nr_samples =
              std::min(static_cast<size_t>(proposed_sampleoffset), batch.nrsamples_total) -
              batch.nrsamples_current;

          if (!nr_samples)
            stream.batches.pop_front();
          else {
            Reference ref;
            ref.nrbytes_offset = batch.nrsamples_current * stream.sample_bytewidth;
            ref.nrbytes_length = nr_samples * stream.sample_bytewidth;
            batch.nrsamples_current += nr_samples;
            ref.buffer_tagged = batch;

            stream.nrsamples_processed += nr_samples;
            stream.nrbytes_pending -= ref.nrbytes_length;
            stream.deficit -= nr_samples / batch.sample_rate;
            manifest.references[identifier].push_back(std::move(ref));

          } // if (nr_samples)
        } // if (proposed > current)
      } // stream.batches.empty
    } // head < size.
  } // identifiers.

  return static_cast<int>(nr_manifests_completed);
}

} // namespace subaligner

} // namespace cthulhu
