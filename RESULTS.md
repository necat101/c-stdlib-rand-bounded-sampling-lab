# RESULTS

Toolchain: /portable-zig/zig, zig 0.14.0, target x86_64-unknown-linux-musl

Python: /python-lab/python3

RAND_MAX=2147483647, source_span=2147483648

default_seed_equivalent: True

same_seed_equal: True

different_seed_differ (local): True

range_invariant passed

modulo 16→6 counts: [3, 3, 3, 3, 2, 2]

modulo 32→10 counts: [4, 4, 3, 3, 3, 3, 3, 3, 3, 3]

power_of_two counts: [2, 2, 2, 2, 2, 2, 2, 2]

top_tail rejection counts: [2, 2, 2, 2, 2, 2], accepted_span=12

bitmask rejection counts: [1, 1, 1, 1, 1, 1]

zero_bound status: 1, rand_calls=0

fisher_yates selected_indices: [5, 0, 1, 2, 1], final_array: [4, 3, 2, 1, 0, 5]

candidate_index: 5, candidate_id: 621

cases: 16, methods: 4, rows: 64

Classifications:
- pass: 13
- expected_error: 1
- local_observation: 1
- toolchain_skip: 0
- context_only: 1
- not_applicable: 48
- fail: 0

Elapsed: 0.001s

Narrow local conclusions only. No randomness validation, no ML validation, no security, no universal portability.
