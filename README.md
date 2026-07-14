# c-stdlib-rand-bounded-sampling-lab

A small deterministic C correctness lab about `rand()`, `srand()`, `RAND_MAX`, repeatability after reseeding, and bounded range reduction. Inspired by HN thread 17599660, “Efficiently Generating a Number in a Range”.

## What this lab does

- exercises C `stdlib.h` `rand()` / `srand()` / `RAND_MAX` via a tiny C helper compiled with `zig cc`
- enumerates exact modulo counts over finite toy domains (0..15, 0..255)
- measures rejection thresholds, accepted-domain uniformity, power-of-two bounds
- demonstrates fixed-low-bit synthetic projection (does NOT describe local `rand()`)
- records local `rand() % 10` counts (10000 samples, seed 12345u) as local_observation only
- enumerates three-item Fisher–Yates shuffle bias with modulo-mapped draws vs accepted draw space
- tiny minibatch index sampler (byte domain → 10 indexes) – index sampling only, no training

## What this lab does NOT do

- does NOT validate a random-number generator
- does NOT validate an ML training pipeline
- does NOT validate statistical quality of a model
- does NOT run testu01, dieharder, practrand, or any statistical battery
- does NOT compare pcg, xoshiro, mersenne twister, or OS randomness
- does NOT establish a fastest method
- does NOT prove `rand()` is secure, statistically suitable for ML, or cross-platform portable
- does NOT train a model, create a dataset, or calculate accuracy/loss/precision/recall/F1/AUC

## Toolchain

- zig 0.14.0 via `zig cc`
- C11, `-O2 -Wall -Wextra -Wpedantic -Werror`
- Python 3.12.3 (stdlib only)
- RAND_MAX: 2147483647

## Cases (20)

zig_compiler_marker · c_rand_api_marker · rand_max_marker · implicit_seed_equals_srand_one_marker · same_seed_replay_marker · seed_reset_prefix_marker · sequence_portability_limit_marker · toy_divisible_modulo_marker · toy_nondivisible_modulo_marker · rejection_threshold_marker · rejection_uniformity_marker · power_of_two_bound_marker · low_bit_projection_marker · bounded_helper_guard_marker · actual_rand_modulo_local_counts_marker · three_item_shuffle_modulo_marker · three_item_shuffle_accepted_draw_space_marker · tiny_minibatch_index_sampler_marker · range_reduction_not_rng_quality_marker · no_global_rng_or_ml_validity_claim_marker

Methods: inspect_toolchain, exercise_c_stdlib, enumerate_mapping, ml_context_observation — 80 rows total.

## Key observations

- implicit `rand()` before any `srand()` behaves as though `srand(1)` – local C library only
- `srand(12345u)` replay: 32 values match exactly after reset (local deterministic replay)
- seed-reset prefix: 8+8 concatenation equals 16-value replay
- C does NOT require identical `rand()` sequences across implementations
- toy divisible: 0..15 mod 4 → [4,4,4,4]
- toy nondivisible: 0..15 mod 6 → [3,3,3,3,2,2]
- rejection threshold (domain 16, bound 6): accepted_limit 12, rejected [12,13,14,15]
- accepted domain 0..11 mod 6 → [2,2,2,2,2,2]
- power-of-two bound 8 over 0..15 → [2]*8
- low-bit projection (synthetic even source): all zeros – does NOT describe local `rand()`
- bounded helper: rejects bound==0, bound>rand_domain, null output
- local `rand() % 10`: 10000 samples at seed 12345u → [1026,998,998,980,968,949,1041,1004,1019,1017] – local_observation only
- shuffle modulo: 16 raw pairs → permutation counts [4,4,2,2,2,2] (biased)
- shuffle accepted: 6 draw pairs → 6 permutations exactly once
- minibatch: 0..255 mod 10 → 0..5 get 26, 6..9 get 25; accepted 0..249 → 25 each

## Range reduction does not establish RNG quality

Exact modulo counts over a complete toy domain prove only properties of that finite mapping. Balanced rejection mapping assumes equiprobable source values. Same-seed replay proves local deterministic replay after resetting the C library state. Same-seed replay does not prove cross-platform sequence portability. Range reduction does not establish the period, unpredictability, independence, equidistribution, or cryptographic suitability of `rand()`. The lab does not run testu01, dieharder, practrand, or an equivalent statistical battery. The lab does not compare pcg and xoshiro. The lab does not establish that the linked article's performance results apply to this machine. The lab does not establish that `rand()` is acceptable for security, scientific simulation, or production ML.

## No global RNG or ML validity claim

This repository does NOT prove: `rand()` is cryptographically secure; `rand()` is statistically suitable for machine learning; `rand()` produces the same sequence on every C implementation; a portable compiler makes the linked C library's rand sequence portable; `srand(seed)` captures all random state in another library or framework; `rand() % n` is detectably harmful for every practical value of n; a small observed count difference is statistically significant; rejection sampling has a finite worst-case number of draws; rejection sampling repairs a biased or predictable underlying generator; a power-of-two bound is safe with every low-bit-defective generator; the synthetic low-bit case describes the local `rand()` implementation; the three-item shuffle is a realistic dataset-shuffling benchmark; the tiny ten-index example measures model quality; the tiny ten-index example is training data; uniform index selection guarantees unbiased learning; random sampling alone validates an ML pipeline; the lab compares pcg, xoshiro, mersenne twister, or operating-system randomness; the lab establishes a fastest method; the hacker news discussion proves the C standard library is badly designed; the linked article proves standard-library abstractions are always over-engineered; one local seeded run validates a production random-number system.

## Why bounded random integers matter to ML-adjacent workflows

Deterministic bounded random indexes are used in: shuffling training examples, sampling minibatches, randomized search / hyperparameter sampling, train/validation splits, reservoir sampling, negative sampling, dropout mask selection, data augmentation choice. This repository demonstrates only the narrow mapping from a bounded integer source to a smaller bounded output range – it does NOT validate training outcomes, convergence, model quality, or statistical properties of any ML system.

## Hacker News thread access

Thread 17599660 was read using the bundled real Hacker News CLI at `/usr/lib/node_modules/openclaw/dist/extensions/hackernews/skills/hackernews/hackernews`, command:

```
python3 ./hackernews get-item --id 17599660
```

Followed by recursive Firebase API fetches for all comment children. Relevant public evidence was captured in `hn_thread_evidence.md` and `hn_comments_sanitized.json` before the sentiment summary was prepared.

### Thread summary

The linked article is “Efficiently Generating a Number in a Range” (pcg-random.org, O'Neill). It focuses on converting an existing random stream into a bounded range – a post-processing / range-reduction problem – not on designing the underlying generator itself.

Commenters distinguished generator quality from bounded mapping: simias (17610542) and throwaway080383 (17610014, 17609614 via dahart) explicitly noted the article is about post-processing a raw RNG output into a bounded integer, not about the RNG scheme itself.

Modulo bias: WorkLifeBalance (17610551) stated “The modulo approach is biased for all ranges which don't divide the full range”. Several commenters agreed bias exists when the source-domain size is not divisible by the requested bound; the magnitude depends on the source domain and the bound.

Over-engineering disagreement: dagenix (17610205, 17610786) objected to the article calling C++ standard library machinery “over-engineered”, arguing “one person's niche use case is another person's main use case” and that the article dismissed support for ranges like [-3,17] while discussing modulo bias at large ranges. vinkelhake (17610626) clarified the C++ distribution must handle a generator whose output range itself might be [3,17], not just producing outputs in that range. Other commenters emphasized that simpler range-reduction code can be appropriate under a narrower generator contract – the right engineering choice depends on the generator contract and application.

Pigeonhole / rejection: modeless (17610982) asked if unbiased bounded output is possible without rejection sampling. dragontamer (17611569), duckerude (17611105, 17611310, 17611438, 17611706, 17612214), frankmcsherry (17611429), and dan-robertson (17613169) discussed the pigeonhole principle: exact unbiased mapping from a fixed-size source to an arbitrary bound generally requires rejection, looping, or retained state – a theoretical argument, not a measurement of the local C library.

Performance anecdote: nerdponx (17609104) reported “RNG was a serious performance bottleneck” in their workload. ballenf (17610662) summarized the article's conclusion as “the PRNG generation method used is usually not the bottleneck, but how you take the PRNG and map it to your desired range” – a comment about surrounding range-reduction costs, not proof that one generator is universally faster.

Generator discussion (pcg / xoshiro / crypto / low-order bits / monte carlo): sdmike1 (17609054), dahart (17609614), throwaway080383 (17610014), smaddox (17610117, 17610446, 17610932), nightcracker (17610299), zeeboo (17611742) debated pcg vs xoshiro, weak low-order bits in Xoroshiro+/Xoshiro+, generator predictability / attacks, and cryptographic unpredictability. Low-order-bit concerns depend on the underlying generator and the operation (e.g. `% 52` passes the lowest bit through). This side discussion is broader thread context – it must NOT be presented as evidence about C's `rand()` implementation on the local machine. A monte carlo reference appeared in the thread but does not establish machine-learning validity.

One thread does not prove that modulo bias matters materially in every application. Deterministic random indexes are relevant to shuffling and sampling but do not validate training outcomes.

Quotes above are paraphrased from public HN comments; see `hn_comments_sanitized.json` for exact text.

## Distinguishing claims

- What the linked PCG article says: how to convert a random stream into a bounded range efficiently and without bias; discusses modulo bias, multiply-and-shift, bitmask-with-rejection, etc.; notes some generators (e.g. Xoroshiro+/Xoshiro+) have weak low-order bits that fail statistical tests.
- What individual HN commenters said: see “Thread summary” above with commenter attribution.
- What C/POSIX actually promises about `rand()`, `srand()`, `RAND_MAX`: per https://pubs.opengroup.org/onlinepubs/9699919799/functions/rand.html – `rand()` returns a pseudo-random integer in [0, RAND_MAX]; `srand(seed)` sets the seed; if `rand()` is called before any `srand()`, it behaves as though `srand(1)` was called; `RAND_MAX` ≥ 32767 per https://pubs.opengroup.org/onlinepubs/9699919799/basedefs/stdlib.h.html; the C standard does NOT require any particular algorithm or cross-implementation sequence portability.
- What the local C implementation does: compiled with zig cc (clang 19.1.7 frontend), RAND_MAX = 2147483647, `srand(1)` implicit behavior confirmed locally, `srand(12345u)` replay matches locally – implementation-specific, not portable.
- What is proven by exhaustive toy source domains: exact finite-domain modulo counts, rejection thresholds, accepted-domain uniformity, shuffle permutation bias – properties of the stated mapping over the stated synthetic domain only.
- What is merely observed from one seeded local `rand()` sequence: the `rand() % 10` counts at seed 12345u – a local_observation, no uniformity claim, no statistical test.

## Reproduce

```
$ZIG_BIN cc -std=c11 -O2 -Wall -Wextra -Wpedantic -Werror rand_lab.c -o rand_lab
python3 -m py_compile run_lab.py test_lab.py
python3 run_lab.py
python3 -m unittest -v
```

See VERIFY.md for clean-clone verification.
