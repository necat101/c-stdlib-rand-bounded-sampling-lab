# c-stdlib-rand-bounded-sampling-lab

Deterministic C standard-library correctness lab for `rand()`, `srand()`, `RAND_MAX`, and bounded integer mapping. No model training, no dataset, no benchmark.

This is a correctness and evidence lab. It is not a benchmark, a randomness certification project, or a machine-learning experiment.

## Scope (narrow)

- C standard-library `rand()` / `srand()` API presence
- Local sequence replay observations (same seed)
- Range invariant checking (`0 ≤ rand() ≤ RAND_MAX`)
- Exact finite enumeration of modulo bias (16→6, 32→10)
- Power-of-two balanced mapping
- Top-tail rejection (16→6, accepted_span=12)
- Bitmask rejection (8→6)
- Zero-bound rejection policy
- Fixed Fisher-Yates index schedule
- Fixed candidate-index selection

The repository does **not**:
- train a model
- download a model or dataset
- perform inference
- calculate loss, accuracy, precision, recall, F1, AUC, etc.
- implement a tokenizer
- implement weighted token sampling
- validate a random-number generator statistically
- test cryptographic security
- benchmark throughput
- prove cross-platform reproducibility

## Bounded random indices and ML-adjacency

Dataset-index shuffling, minibatch ordering, reservoir selection, negative-sample indices, bootstrap indices, candidate selection, and randomized evaluation order are machine-learning-adjacent because they routinely consume bounded uniform integers. This repository demonstrates only fixed index-schedule reconstruction and fixed candidate-index mapping over synthetic finite domains. It does not validate a model, dataset, tokenizer, sampler, probability distribution, training process, inference engine, or statistical test suite.

## What the linked article says

Source: https://www.pcg-random.org/posts/bounded-rands.html

The article discusses correctness and performance tradeoffs in bounded integer generation, distinguishing:

- classic modulo mapping
- floating-point multiplication
- integer multiplication
- division with rejection
- threshold-based modulo rejection
- multiplication with rejection
- bitmask rejection
- weak low-order bits
- source ranges vs requested bounds
- benchmark sensitivity

The article's benchmark rankings, generator comparisons, and platform-specific observations are the author's measurements, not universal results, and are not reproduced here.

This lab uses integer arithmetic for its accepted bounded result. Floating-point multiplication is discussed in documentation only.

## C standard vs local library

The C standard (https://www.open-std.org/jtc1/sc22/wg14/www/docs/n3220.pdf) specifies `rand()`, `srand()`, and `RAND_MAX ≥ 32767`, but does not mandate a specific algorithm.

POSIX `rand()`/`srand()`: https://pubs.opengroup.org/onlinepubs/9799919799/functions/rand.html  
POSIX `<stdlib.h>`: https://pubs.opengroup.org/onlinepubs/9799919799/basedefs/stdlib.h.html

This repository records local `RAND_MAX` and local sequence observations only. It does not identify the underlying libc algorithm, does not claim cross-platform reproducibility, and distinguishes deterministic same-implementation sequence observations from cross-platform reproducibility.

## Distinctions maintained

- C standard specification vs local C library behavior
- pseudorandom-number generator vs bounded-range mapping
- deterministic exhaustive source-domain enumeration vs statistical test of a generator
- repository-owned range-mapping policy vs standard-library behavior
- mathematically balanced finite mapping vs claim that the underlying generator is statistically high quality
- uniform candidate-index selection vs weighted token sampling
- fixed Fisher-Yates index schedule vs validated dataset-shuffling pipeline
- machine-learning-adjacent examples vs actual model training/inference/evaluation

The repository does not prove:
- that the selected `rand()` implementation uses a particular algorithm
- that `rand()` is statistically high quality
- that `rand()` is cryptographically secure
- that `rand()` is suitable for passwords, keys, tokens, salts, or nonces
- cross-platform sequence reproducibility
- that different seeds produce different sequences (universal)
- period size, independence, absence of correlations, or uniformity of the underlying generator
- that a balanced finite mapping produces balanced real samples from a biased source
- that modulo is always inappropriate, or that rejection is always required/faster/slower
- a finite worst-case retry count for rejection sampling
- that bitmask rejection is optimal
- that the article's benchmark results apply locally
- that low-order bits are strong
- that the selected libc matches glibc, musl, BSD libc, or Windows
- that a fixed Fisher-Yates trace validates a dataset pipeline
- that shuffled order improves training
- that candidate-index selection implements language-model sampling
- that a uniform candidate choice represents a model probability distribution
- negative/reservoir/bootstrap sampling validation
- any model/dataset/training/inference/quality/statistical/ML/security/portability/production claim

## Hacker News thread access

```
hackernews get-item --id 17599660
```

Relevant public evidence was captured before the discussion summary was written.

See `hn_thread_evidence.md` and `hn_comments_sanitized.json`.

### Discussion summary

The thread is https://news.ycombinator.com/item?id=17599660 discussing "Efficiently Generating a Number in a Range" (PCG bounded-rands article).

- **dagenix** objected to dismissing general range handling as "over-engineered", arguing algorithms should be matched to use cases, and that labeling general support as over-engineering does not add to discussion.
- **vinkelhake** clarified that the unusual range in the discussion referred to the generator's output range rather than the requested result range.
- **worklifebalance** emphasized that modulo mapping is biased whenever the source-domain size is not divisible by the requested range.
- **kazinator** described masking to a power-of-two range and rejecting values outside the target range (referred to as "Bitmask" in the article).
- **jgtrosh** and **throwaway080383** debated the average rejection probability, then corrected the calculation.
- **bmm6o** questioned what distribution over requested ranges that average assumed.
- **simias** separated random-generator quality from the problem of converting raw output into an unbiased bounded integer.
- **ballenf** said the surrounding range-reduction code can matter more than the generator in some workloads.
- **adrianmonk** suggested that a larger mask can sometimes reduce the rejection rate.
- **modeless** asked whether an exact arbitrary-range method can avoid a retry loop or impose a finite retry cap.
- **dragontamer** and **duckerude** used the pigeonhole principle to explain the mapping problem.
- **frankmcsherry** and **dan-robertson** gave more formal explanations of why a fixed finite number of equally likely source outcomes cannot represent every requested uniform range exactly.
- **sdmike1** suggested xoshiro-family generators.
- **dahart** warned that weak low-order bits matter when modulo passes those bits directly into the result.

The thread does not prove that one bounded-generation method is best for every source generator, every requested range, every compiler, or every application.

This lab uses exact finite enumeration rather than empirical frequency claims.

## Toolchain

- Zig: https://ziglang.org/
- Portable install: https://ziglang.org/learn/getting-started/
- Compiler invoked via `"$ZIG_BIN" cc`

## Results

See `RESULTS.md` for machine-generated summaries. Sixteen cases, four methods, sixty-four rows.

## Verification

See `VERIFY.md`.
