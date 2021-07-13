// Copyright 2004-present Facebook. All Rights Reserved.

#pragma once

#include <cassert>
#include <iterator>
#include <memory>
#include <numeric>
#include <queue>
#include <set>
#include <unordered_map>
#include <utility>
#include <vector>

// Thread-Safety Consideration
// ===========================
//
// 1. The method enroll is not thread-safe and must be called sequentially.
// 2. The method enqueue can be called on different streams concurrently.
// 3. The method request must be called sequentially.
// 4. The method finalizeOne is not thread-safe.
// 5. The method finalize is not thread-safe.
// 6. The method align is definitely not thread-safe.

namespace cthulhu {

namespace subaligner {

using Buffer = std::shared_ptr<uint8_t>;

struct Duration {
  double start_time;
  double end_time;
};

struct BufferDurational {
  Buffer buffer;
  Duration duration;
};

struct Statistics {
  size_t samples_emitted = 0;
  size_t samples_received = 0;
  size_t batches_emitted = 0;
  size_t batches_received = 0;
};

class Aligner;

struct StreamInterface {
  // Allow for mutual access of protected internal methods.
  friend class Aligner;
  explicit StreamInterface(Aligner* aligner, int identifier);

  //! Retrieve the index of this data stream.
  int index() const;
  //! Release this control interface and its associated stream.
  void release();
  //! Designate this stream as the primary stream for automatic duration request.
  void primarize();
  //! Check if this is the primary stream
  bool isPrimary();
  // Retrieve an estimation of the sample period.
  double obtainSamplePeriod(int multiplier = 1) const;
  //! Feed a stamped batch of samples to the aligner for alignment.
  void feed(
      const Buffer& buf,
      size_t buf_size,
      double start_time,
      double end_time = -1.0,
      double surrogate_timestamp = -1.0);
  //! Returns stream statistics.
  Statistics getStats() const;

 protected:
  Aligner* aligner_;
  //!< A pointer to the aligner that's processing all the alignment stuff
  int identifier_; //!< The identifier of the stream whose access is exposed via this interface.
};

struct BufferDurationalTagged {
  double sample_rate; //!< The number of samples per unit time (second).
  size_t sequence_number; //!< A sequence number for this buffer within some stream.
  size_t nrsamples_total; //!< The total number of samples represented by this buffer.
  size_t nrsamples_current; //!< The number of samples that are considered to have been used.
  Duration duration_unadjusted; //!< The raw duration provided by the invoker, without adjustment.
  BufferDurational
      buffer_durational; //!< The managed buffer stamped with a duration, possibly adjusted.
};

struct Reference {
  size_t nrbytes_offset;
  size_t nrbytes_length;
  BufferDurationalTagged buffer_tagged;
};

struct Manifest {
  Duration duration;
  std::set<int> completed_streams;
  std::unordered_map<int, std::vector<Reference>> references;
};

/* Aligner: Requirements and Assumptions
 * =====================================
 *
 *
 * 1. The requested durations should not overlap and their start times should be
 *    monotonically increasing. Otherwise, the behavior is still well defined, but
 *    may not reflect the intended alignment policy: since each sample for each
 *    stream is used exactly once, durations that have overlap with previously
 *    requested ones will not reuse the samples that fall into the overlap region;
 *    also references to used samples are effectively dropped, such that durations
 *	  that are old may have nothing aligned to it at all. Note that sometimes the
 *    presence of noice on the timestamps will slightly violate this assumption, but
 *    typically only a small number of samples are affected on the noisy band.
 *
 * 2. The linespans for sample batches for each stream should not overlap and their
 *    start times should be monotonically increasing. This ensures that each manifest,
 *    in service of the requested durations mentioned in 1. have samples whose time-stamps
 *    are also monotonically increasing. In service of a requested duration, references
 *	  to praticular segments into the batches that are considered inclusive (see 5.)
 *	  are added to the manifest based on the order of receipt of the batches, not
 *	  necessarily their actual start times. This means that, if the assumption is violated,
 *	  certain samples that are temporally after some other samples, although received earlier
 *	  will appear earlier in the list of references in the manifest; the samples in the manifest
 *    for that particular stream no longer have monotonically increasing timestamps. Note that
 *    sometimes the presence of noise on the timestamps will slightly make the linespans
 *    overlap, but since each sample is used exactly once, this should have little impact.
 *
 * 3. The sizes for all the samples delivered on a particular stream must be
 *    identical. Otherwise, since the aligned batches are emitted asychronously
 *    with the incoming batches, some mechanism must be in place to track these
 *    sizes and possibly their semantics. This increases the complexity of the
 *    class (albeit making perfect sense in terms of the alignment operation),
 *    yet does not have a good use case for it to be justified. This is forcefully
 *    restricted, as the user cannot specify the number of samples for each batch;
 *    the number of bytes, combined with the sample byte width specified on instantiation,
 *    uniquely dictates the number of samples. If the number of bytes is not a
 *    multiple of the byte width, assertion may be raised.
 *
 * 4. Samples in each individual batch have identical lifespans (i.e., end time
 *    minus start time) and are temporally contiguous. This means that the duration
 *    of the batch is evenly distributed over all the samples. To specify different
 *    lifespans for individual samaples, use multiple batches instead.
 *
 * 5. A sample is considered to be inclusive of a duration if the middle point of
 *    its lifespan is. Specifying another point would destory the symmetry semantics;
 *    specifying two symmetric points with respect to the middle point, will either
 *    lead to one sample being automatically aligned with two successive requested
 *    durations, or one part of the duration not having well-defined semantics.
 *
 */

class Aligner {
  /* Metronome: Additional Assumption
   * ================================
   *
   * 6. The rate, defined as the number of samples (fractional) within an arbitrarily small
   *    duration, divided by that duration, is fixed for all the samples from a particular
   *    stream. This means that: a) there should be no gap in the stream, b) the lifespan (
   *    end time - start time) is identical for all samples, c) no two samples can have
   *    overlapping lifespans. This should be the predominant situation for most streams.
   *
   * This class essentially assumes a fixed rate and estimates an end time for each batch,
   * given its start time and a history of start times and batch sizes, thus eliminating
   * the need for the user to perform this calculation.
   *
   */

  struct Metronome {
    //! Construct a metronome of a particular byte width and nominal rate.
    explicit Metronome(size_t _sample_bytewidth, double _nominal_rate);
    //! Estimate the end time of this batch and update the corresponding field.
    void propagate(BufferDurationalTagged& batch);
    //! Obtain the current estimation of the sample rate.
    double obtainSampleRateEstimate() const;
    //! Resets frame rate estimation
    void reset();

   protected:
    //! Update the estimation of the initial time reference and the sample rate.
    void update(const BufferDurationalTagged& batch);

    struct Fraction {
      double numerator = 0;
      double denominator = 0;
      double decimal = 0;
    };

    size_t sample_bytewidth; //!< The width of each individual sample in bytes.
    double nrsamples_cumulative =
        0; //!< The cumulative number of samples this metronome has ever received.
    double nominal_rate = 0;
    Fraction
        reference_time_estimate; //!< An estimation of the reference time (time base) of the stream.
    Fraction sample_rate_estimate; //!< An estimation of the sample rate of the stream.
    BufferDurationalTagged
        previous_batch; //!< A container for some information in the previous batch. No buffer.
  };

 public:
  struct Stream {
    Statistics stats; //!< A suite of statistics on the samples received and emitted.
    size_t nrbytes_pending; //!< The total number of bytes that have been received but not yet
                            //!< aligned to anything.
    size_t nrsamples_processed; //!< The number of samples in the currently active batch that have
                                //!< been aligned to something.
    int manifest_upstream_index; //!< The index of the manifest in the active manifest queue that
                                 //!< this stream is working on.
    double deficit; //!< The sum of requested durations that cannot be serviced due to lack of data
                    //!< on this stream.

    int identifier; //!< An unique identifier to this stream.
    size_t sample_bytewidth; //!< The size of one sample in bytes (that shall remain unchanged over
                             //!< the entire session).
    double timestamp_offset; //!< An offset that should be applied to all start and end times for
                             //!< incoming batches of samples.
    std::shared_ptr<Metronome>
        metronome; //!< An Discretional metronome that produces an estimation of the global sample
                   //!< rate and regulates the timestamps.
    std::deque<BufferDurationalTagged> batches; //!< A queue of batches to be aligned.
  };

  // This grants access to the enqueue internal method.
  friend struct StreamInterface;

  //! Enroll a stream into the aligner.
  StreamInterface* enroll(size_t sample_bytewidth, double timestamp_offset);
  //! Enroll a stream that has a fixed nominal rate into the aligner.
  StreamInterface* enroll(size_t sample_bytewidth, double nominal_rate, double timestamp_offset);
  //! Request references to samples within a particular duration, should be followed by a call to
  //! align
  void request(double start_time, double end_time);
  //! Forcifully finalize currently active manifests despite their completion status.
  int finalize(int nr_manifests = 1);
  //! Finalize all the manifests before the specified time-point regardless of their completion
  //! status.
  int finalizeBefore(double time_point);
  //! Attempt alignment on the stream corresponding to the identifier hint.
  int align(int identifier_hint = -1);

  //! Retrieve a list of manifests that are currently available.
  std::vector<Manifest> retrieve() {
    decltype(completed_manifests_) other;
    other.swap(completed_manifests_);
    nr_manifests_completed = 0;
    return other;
  }

  //! Flushes content of all streams
  void flush();

 protected:
  //! Forcifully finalize the currently active manifest if exists regardless of its completion
  //! status.
  int finalizeOne();
  //! Enqueue a stamped batch of samples for some stream
  void enqueue(
      int identifier,
      const Buffer& buf,
      size_t buf_size,
      double start_time,
      double end_time = -1.0,
      double surrogate_timestamp = -1.0);
  //! Designate the stream with the specified identifier as the primary stream.
  void primarize(int identifier);
  //! Check if the sstream with specified identifier is the primary stream
  bool isPrimary(int identifier) const;
  //! Release the control interface and its associated stream.
  void release(int identifier);
  //! Obtain the sample period estimated to the best knowledge.
  double obtainSamplePeriod(int identifier, int multiplier = 1) const;
  //! Returns stream statistics.
  Statistics getStats(int identifier) const;

  int primary_stream_id;
  size_t nr_manifests_emitted =
      0; //!< The number of manifests that have been emitted by this aligner.
  size_t nr_manifests_completed = 0; //!< The number of manifests that have been completed.

  std::deque<Manifest>
      active_manifests_; //!< A queue of manifests that are currently open for fulfillment.
  std::vector<Manifest>
      completed_manifests_; //!< A list of manifests that are fully serviced and ready for shipment.
  std::unordered_map<int, Stream*>
      registry_; //!< A table of streams that have been enrolled with this aligner.
  std::unordered_map<int, StreamInterface*>
      stream_interfaces_; //!< A storage for all the stream interfaces.
};

} // namespace subaligner

} // namespace cthulhu
