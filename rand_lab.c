#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <inttypes.h>

/* bounded helper that returns status rather than modulo for invalid request */
static int bounded_rand_uintmax(uintmax_t bound, uintmax_t *out) {
    uintmax_t rand_domain = (uintmax_t)RAND_MAX + 1;
    if (bound == 0) return 1;
    if (bound > rand_domain) return 2;
    if (out == NULL) return 3;
    /* valid bound – use rejection + modulo; comments state this does NOT repair defects in the underlying RNG */
    uintmax_t limit = rand_domain - (rand_domain % bound);
    uintmax_t r;
    do {
        r = (uintmax_t)rand();
    } while (r >= limit);
    *out = r % bound;
    return 0;
}

int main(void) {
    /* implicit_seed_equals_srand_one */
    int implicit_prefix[16];
    for (int i = 0; i < 16; i++) implicit_prefix[i] = rand();
    srand(1);
    int srand1_prefix[16];
    for (int i = 0; i < 16; i++) srand1_prefix[i] = rand();

    /* same_seed_replay */
    srand(12345u);
    int replay_a[32];
    for (int i = 0; i < 32; i++) replay_a[i] = rand();
    srand(12345u);
    int replay_b[32];
    for (int i = 0; i < 32; i++) replay_b[i] = rand();

    /* seed_reset_prefix */
    srand(12345u);
    int seg1[8], seg2[8];
    for (int i = 0; i < 8; i++) seg1[i] = rand();
    for (int i = 0; i < 8; i++) seg2[i] = rand();
    srand(12345u);
    int seg_full[16];
    for (int i = 0; i < 16; i++) seg_full[i] = rand();

    /* actual_rand_modulo_local_counts */
    srand(12345u);
    int mod10_counts[10] = {0};
    for (int i = 0; i < 10000; i++) {
        int r = rand();
        mod10_counts[r % 10]++;
    }

    /* bounded_helper_guard – actually exercise it */
    uintmax_t rand_domain = (uintmax_t)RAND_MAX + 1;
    uintmax_t dummy_out;
    int guard_zero = bounded_rand_uintmax(0, &dummy_out);
    int guard_oversize = bounded_rand_uintmax(rand_domain + 1, &dummy_out);
    int guard_null = bounded_rand_uintmax(10, NULL);
    /* valid call should succeed */
    int guard_valid = bounded_rand_uintmax(10, &dummy_out);

    printf("{\n");
    printf("\"RAND_MAX\":%d,\n", RAND_MAX);
    printf("\"sizeof_int\":%zu,\n", sizeof(int));
    printf("\"rand_domain_size\":%" PRIuMAX ",\n", rand_domain);
    printf("\"implicit_prefix\":[");
    for (int i = 0; i < 16; i++) { if(i)printf(","); printf("%d",implicit_prefix[i]); }
    printf("],\n");
    printf("\"srand1_prefix\":[");
    for (int i = 0; i < 16; i++) { if(i)printf(","); printf("%d",srand1_prefix[i]); }
    printf("],\n");
    printf("\"replay_a\":[");
    for (int i = 0; i < 32; i++) { if(i)printf(","); printf("%d",replay_a[i]); }
    printf("],\n");
    printf("\"replay_b\":[");
    for (int i = 0; i < 32; i++) { if(i)printf(","); printf("%d",replay_b[i]); }
    printf("],\n");
    printf("\"seg1\":[");
    for (int i = 0; i < 8; i++) { if(i)printf(","); printf("%d",seg1[i]); }
    printf("],\n");
    printf("\"seg2\":[");
    for (int i = 0; i < 8; i++) { if(i)printf(","); printf("%d",seg2[i]); }
    printf("],\n");
    printf("\"seg_full\":[");
    for (int i = 0; i < 16; i++) { if(i)printf(","); printf("%d",seg_full[i]); }
    printf("],\n");
    printf("\"mod10_counts\":[");
    for (int i = 0; i < 10; i++) { if(i)printf(","); printf("%d",mod10_counts[i]); }
    printf("],\n");
    printf("\"guard_zero_status\":%d,\n", guard_zero);
    printf("\"guard_oversize_status\":%d,\n", guard_oversize);
    printf("\"guard_null_status\":%d,\n", guard_null);
    printf("\"guard_valid_status\":%d\n", guard_valid);
    printf("}\n");
    return 0;
}
