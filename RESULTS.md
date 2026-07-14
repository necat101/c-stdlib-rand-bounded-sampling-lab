# Results – c-stdlib-rand-bounded-sampling-lab

zig: /portable-zig/.local/zig/zig version 0.14.0

zig cc: clang version 19.1.7 (https://github.com/ziglang/zig-bootstrap 1c3c59435891bc9caf8cd1d3783773369d191c5f)

compile flags: -std=c11 -O2 -Wall -Wextra -Wpedantic -Werror (c11)

python: 3.12.3

platform: Linux-6.17.0-1009-aws-x86_64-with-glibc2.39

RAND_MAX: 2147483647, rand_domain_size: 2147483648

cases: 20, methods: 4, rows: 80

classifications: pass=15, expected_error=0, local_observation=3, context_only=4, toolchain_skip=0, not_applicable=58, fail=0

implicit srand(1): implicit rand() prefix equals srand(1) prefix locally.

same_seed_replay: srand(12345u) replay matches, 32 values.

seed_reset_prefix: 8+8 concatenation equals 16-value replay.

sequence_portability: C does not require identical rand() sequences across implementations.

toy_divisible_modulo: source 0..15, bound 4, counts [4, 4, 4, 4].

toy_nondivisible_modulo: source 0..15, bound 6, counts [3, 3, 3, 3, 2, 2], quotient 2 remainder 4.

rejection_threshold: accepted_limit 12, rejected [12, 13, 14, 15].

rejection_uniformity: counts [2, 2, 2, 2, 2, 2], each output 2 representations.

power_of_two_bound: bound 8, counts [2, 2, 2, 2, 2, 2, 2, 2].

low_bit_projection: synthetic even source → all zeros, counts [8, 0] – does NOT describe local rand().

bounded_helper_guard: zero=1, oversize=2, null=3, valid=0 – rejects invalid bounds.

actual_rand_modulo_local_counts: seed 12345u, 10000 samples, bound 10, counts [1026, 998, 998, 980, 968, 949, 1041, 1004, 1019, 1017] – local_observation only, no uniformity claim.

three_item_shuffle_modulo: 16 raw pairs, permutation counts multiset [2, 2, 2, 2, 4, 4] (biased).

three_item_shuffle_accepted_draw_space: 6 accepted pairs → 6 permutations exactly once.

tiny_minibatch_index_sampler: byte domain 0..255 mod 10 → [26, 26, 26, 26, 26, 26, 25, 25, 25, 25] (0..5 get 26, 6..9 get 25), rejected [250, 251, 252, 253, 254, 255], accepted counts [25, 25, 25, 25, 25, 25, 25, 25, 25, 25] – index sampling only, no training.

range_reduction_not_rng_quality: exact modulo counts prove only mapping properties; balanced rejection assumes equiprobable source; same-seed replay is local only; range reduction does not establish period, unpredictability, independence, equidistribution, or cryptographic suitability; no testu01/dieharder/practrand; no pcg/xoshiro comparison; no performance claims; rand() not validated for security/simulation/production ML.

no_global_rng_or_ml_validity_claim: repository does NOT prove rand() is cryptographically secure; statistically suitable for ML; cross-platform portable; srand captures external framework state; rand()%n is always harmful; small count differences are significant; rejection has finite worst-case draws; rejection repairs biased generator; power-of-two is safe with every low-bit-defective generator; synthetic low-bit case describes local rand(); three-item shuffle is a realistic benchmark; ten-index example measures model quality / is training data; uniform index selection guarantees unbiased learning; random sampling validates ML pipeline; lab compares pcg/xoshiro/mt/os randomness; establishes fastest method; HN thread proves C stdlib badly designed; linked article proves stdlib abstractions always over-engineered; one local run validates production RNG.

failures: 0, toolchain_skips: 0

total runtime: 0.168s

