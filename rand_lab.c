#include <stddef.h>
#include <stdint.h>
#include <inttypes.h>
#include <stdlib.h>
#include <limits.h>
#include <stdio.h>
#include <string.h>
#include <errno.h>

static __attribute__((unused)) uintmax_t modulo_map_u(uintmax_t src, uintmax_t bound) {
    return src % bound;
}

static __attribute__((unused)) int top_tail_accept_u(uintmax_t src, uintmax_t source_span, uintmax_t bound) {
    uintmax_t accepted_span = source_span - (source_span % bound);
    return src < accepted_span;
}

static __attribute__((unused)) uintmax_t map_accepted_u(uintmax_t src, uintmax_t bound) {
    return src % bound;
}

static int bounded_rand_reject(int *out, uintmax_t bound, uintmax_t *rand_calls, uintmax_t *rem_ops, uintmax_t *div_ops) {
    (void)div_ops;
    if (bound == 0) return 1;
    uintmax_t source_span = (uintmax_t)RAND_MAX + 1;
    if (bound > source_span) return 2;
    uintmax_t accepted_span = source_span - (source_span % bound);
    *rem_ops += 1;
    while (1) {
        int r = rand();
        (*rand_calls)++;
        if ((uintmax_t)r < accepted_span) {
            (*rem_ops)++;
            *out = (int)(r % (int)bound);
            return 0;
        }
    }
}

static uint32_t hash_seq(const int *a, size_t n) {
    uint32_t h = 2166136261u;
    for (size_t i=0;i<n;i++) {
        h ^= (uint32_t)a[i];
        h *= 16777619u;
    }
    return h;
}

int main(void) {
    printf("{\n");
    printf("\"__STDC_VERSION__\": ");
#ifdef __STDC_VERSION__
    printf("%ld", (long)__STDC_VERSION__);
#else
    printf("null");
#endif
    printf(",\n");
    printf("\"CHAR_BIT\": %d,\n", CHAR_BIT);
    printf("\"sizeof_int\": %zu,\n", sizeof(int));
    printf("\"sizeof_unsigned_int\": %zu,\n", sizeof(unsigned int));
    printf("\"sizeof_uintmax_t\": %zu,\n", sizeof(uintmax_t));
    printf("\"sizeof_size_t\": %zu,\n", sizeof(size_t));
    printf("\"RAND_MAX\": %d,\n", RAND_MAX);
    printf("\"RAND_MAX_ge_32767\": %s,\n", RAND_MAX >= 32767 ? "true" : "false");
    printf("\"source_span\": %" PRIuMAX ",\n", (uintmax_t)RAND_MAX + 1);

    int (*rand_fp)(void) = rand;
    void (*srand_fp)(unsigned int) = srand;
    (void)rand_fp; (void)srand_fp;
    printf("\"rand_srand_assignable\": true,\n");

    /* default_seed_equivalence_marker */
    int default_seq[8];
    for (int i=0;i<8;i++) default_seq[i] = rand();
    srand(1);
    int srand1_seq[8];
    for (int i=0;i<8;i++) srand1_seq[i] = rand();
    printf("\"default_seed_seq\": [");
    for (int i=0;i<8;i++) printf("%s%d", i?",":"", default_seq[i]);
    printf("],\n");
    printf("\"srand1_seq\": [");
    for (int i=0;i<8;i++) printf("%s%d", i?",":"", srand1_seq[i]);
    printf("],\n");
    int default_eq = 1;
    for (int i=0;i<8;i++) if (default_seq[i] != srand1_seq[i]) default_eq = 0;
    printf("\"default_seed_equivalent\": %s,\n", default_eq ? "true" : "false");

    /* same_seed_replay_marker */
    srand(12345);
    int replay_a[16];
    for (int i=0;i<16;i++) replay_a[i] = rand();
    srand(12345);
    int replay_b[16];
    for (int i=0;i<16;i++) replay_b[i] = rand();
    printf("\"same_seed_a\": [");
    for (int i=0;i<16;i++) printf("%s%d", i?",":"", replay_a[i]);
    printf("],\n\"same_seed_b\": [");
    for (int i=0;i<16;i++) printf("%s%d", i?",":"", replay_b[i]);
    printf("],\n");
    printf("\"same_seed_hash_a\": %u,\n", hash_seq(replay_a,16));
    printf("\"same_seed_hash_b\": %u,\n", hash_seq(replay_b,16));
    int same_eq = 1;
    for (int i=0;i<16;i++) if (replay_a[i] != replay_b[i]) same_eq = 0;
    printf("\"same_seed_equal\": %s,\n", same_eq ? "true":"false");

    /* different_seed_local_observation_marker */
    srand(12345);
    int diff_a[16];
    for (int i=0;i<16;i++) diff_a[i] = rand();
    srand(54321);
    int diff_b[16];
    for (int i=0;i<16;i++) diff_b[i] = rand();
    printf("\"diff_seed_a\": [");
    for (int i=0;i<16;i++) printf("%s%d", i?",":"", diff_a[i]);
    printf("],\n\"diff_seed_b\": [");
    for (int i=0;i<16;i++) printf("%s%d", i?",":"", diff_b[i]);
    printf("],\n");
    printf("\"diff_seed_hash_a\": %u,\n", hash_seq(diff_a,16));
    printf("\"diff_seed_hash_b\": %u,\n", hash_seq(diff_b,16));
    int diff_ne = 0;
    for (int i=0;i<16;i++) if (diff_a[i] != diff_b[i]) { diff_ne = 1; break; }
    printf("\"diff_seed_differ\": %s,\n", diff_ne ? "true":"false");

    /* rand_range_invariant_marker */
    srand(7);
    int range_seq[128];
    int min_v = RAND_MAX, max_v = 0;
    int all_ge0 = 1, all_le_max = 1;
    for (int i=0;i<128;i++) {
        int v = rand();
        range_seq[i] = v;
        if (v < min_v) min_v = v;
        if (v > max_v) max_v = v;
        if (v < 0) all_ge0 = 0;
        if (v > RAND_MAX) all_le_max = 0;
    }
    printf("\"range_min\": %d,\n", min_v);
    printf("\"range_max\": %d,\n", max_v);
    printf("\"range_all_ge0\": %s,\n", all_ge0 ? "true":"false");
    printf("\"range_all_le_rand_max\": %s,\n", all_le_max ? "true":"false");
    printf("\"range_hash\": %u,\n", hash_seq(range_seq,128));

    /* zero_bound_rejection_marker via bounded_rand_reject */
    uintmax_t rcalls=0, rem_ops=0, div_ops=0;
    int out_val = -1;
    int status = bounded_rand_reject(&out_val, 0, &rcalls, &rem_ops, &div_ops);
    printf("\"zero_bound_status\": %d,\n", status);
    printf("\"zero_bound_rand_calls\": %" PRIuMAX ",\n", rcalls);
    printf("\"zero_bound_rem_ops\": %" PRIuMAX ",\n", rem_ops);
    printf("\"zero_bound_div_ops\": %" PRIuMAX ",\n", div_ops);
    printf("\"zero_bound_output_written\": false\n");
    printf("}\n");
    return 0;
}
