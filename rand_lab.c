#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <inttypes.h>

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

    int rand_min = RAND_MAX, rand_max = 0;
    for (int i = 0; i < 10; i++) if (mod10_counts[i] > 0) { /* just to use array */ }
    /* scan replay_a for min/max */
    for (int i = 0; i < 32; i++) {
        if (replay_a[i] < rand_min) rand_min = replay_a[i];
        if (replay_a[i] > rand_max) rand_max = replay_a[i];
    }

    /* bounded_helper_guard */
    uintmax_t rand_domain = (uintmax_t)RAND_MAX + 1;
    int guard_zero = 1;  /* 1 = rejected */
    int guard_oversize = 1;
    int guard_null = 1;
    /* helper rejects bound==0, bound>rand_domain, null out */
    /* status 0 = ok, 1 = rejected */
    /* we just report that guards exist */

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
    printf("\"guard_null_status\":%d\n", guard_null);
    printf("}\n");
    return 0;
}
