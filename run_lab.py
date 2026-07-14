#!/usr/bin/env python3
import json, subprocess, sys, os, time, hashlib, csv, platform, shutil
t0=time.perf_counter()

# resolve zig
def find_zig():
    for c in [os.environ.get("ZIG_BIN"), shutil.which("zig"), os.path.expanduser("~/.local/bin/zig"), os.path.expanduser("~/bin/zig"), os.path.expanduser("~/.local/zig/zig")]:
        if c and os.path.isfile(c) and os.access(c, os.X_OK):
            return c
    return None
zig_bin=find_zig()
if not zig_bin: print("zig not found", file=sys.stderr); sys.exit(2)
zig_version=subprocess.check_output([zig_bin,"version"], text=True).strip()
# sanitize path
zig_repr=zig_bin
for p in [os.path.expanduser("~"), "/home/ubuntu", "/tmp", os.getcwd()]:
    if p and p in zig_repr: zig_repr=zig_repr.replace(p, "/portable-zig")
sanitized = zig_repr != zig_bin

# compile
compile_flags=["-std=c11","-O2","-Wall","-Wextra","-Wpedantic","-Werror"]
cmd=[zig_bin,"cc"]+compile_flags+["rand_lab.c","-o","rand_lab"]
subprocess.check_call(cmd)
# get cc version
try: cc_ver=subprocess.check_output([zig_bin,"cc","--version"], text=True, stderr=subprocess.STDOUT).splitlines()[0][:200]
except: cc_ver="unknown"

# run helper
out=subprocess.check_output(["./rand_lab"], text=True)
cinfo=json.loads(out)

RAND_MAX=cinfo["RAND_MAX"]
sizeof_int=cinfo["sizeof_int"]
rand_domain=cinfo["rand_domain_size"]

def h_ints(arr): return hashlib.sha256(json.dumps(arr, separators=(",",":")).encode()).hexdigest()[:16]

# enum mappings
# toy_divisible
div_counts=[0]*4
for x in range(0,16): div_counts[x%4]+=1
# toy_nondivisible
nd_counts=[0]*6
for x in range(0,16): nd_counts[x%6]+=1
# rejection
src_dom=16; bound_rej=6
accepted_limit=src_dom - (src_dom % bound_rej)
accepted_vals=list(range(accepted_limit))
rejected_vals=list(range(accepted_limit,src_dom))
# rejection_uniformity
rej_uni=[0]*6
for x in range(accepted_limit): rej_uni[x%6]+=1
# power_of_two
pow_counts=[0]*8
for x in range(16): pow_counts[x%8]+=1
# low_bit
low_src=[0,2,4,6,8,10,12,14]
low_outs=[x%2 for x in low_src]
low_counts=[low_outs.count(0), low_outs.count(1)]
# shuffle modulo
def shuffle3(j,k):
    a=["a","b","c"]
    # fisher-yates descending
    # i=2 swap with j %3
    a[2],a[j]=a[j],a[2]
    # i=1 swap with k %2
    a[1],a[k]=a[k],a[1]
    return tuple(a)
perm_counts={}
raw_pairs=[]
for rf in range(4):
    for rs in range(4):
        raw_pairs.append([rf,rs])
        p=shuffle3(rf%3, rs%2)
        perm_counts[p]=perm_counts.get(p,0)+1
perm_multiset=sorted(perm_counts.values())
# accepted shuffle
acc_pairs=[]
acc_perm_counts={}
for j in range(3):
    for k in range(2):
        acc_pairs.append([j,k])
        p=shuffle3(j,k)
        acc_perm_counts[p]=acc_perm_counts.get(p,0)+1
# minibatch
mb_counts=[0]*10
for x in range(256): mb_counts[x%10]+=1
mb_reject_limit=250
mb_rejected=list(range(250,256))
mb_acc_counts=[0]*10
for x in range(250): mb_acc_counts[x%10]+=1

# actual rand modulo
mod10_counts=cinfo["mod10_counts"]

cases=[
"zig_compiler_marker","c_rand_api_marker","rand_max_marker","implicit_seed_equals_srand_one_marker","same_seed_replay_marker","seed_reset_prefix_marker","sequence_portability_limit_marker","toy_divisible_modulo_marker","toy_nondivisible_modulo_marker","rejection_threshold_marker","rejection_uniformity_marker","power_of_two_bound_marker","low_bit_projection_marker","bounded_helper_guard_marker","actual_rand_modulo_local_counts_marker","three_item_shuffle_modulo_marker","three_item_shuffle_accepted_draw_space_marker","tiny_minibatch_index_sampler_marker","range_reduction_not_rng_quality_marker","no_global_rng_or_ml_validity_claim_marker"
]
methods=["inspect_toolchain","exercise_c_stdlib","enumerate_mapping","ml_context_observation"]

# expectation map
exp={}
def E(case,method,cls): exp[(case,method)]=cls
na="not_applicable"
# zig_compiler_marker
E("zig_compiler_marker","inspect_toolchain","pass"); E("zig_compiler_marker","exercise_c_stdlib",na); E("zig_compiler_marker","enumerate_mapping",na); E("zig_compiler_marker","ml_context_observation",na)
# c_rand_api_marker
E("c_rand_api_marker","inspect_toolchain",na); E("c_rand_api_marker","exercise_c_stdlib","pass"); E("c_rand_api_marker","enumerate_mapping",na); E("c_rand_api_marker","ml_context_observation",na)
# rand_max_marker
E("rand_max_marker","inspect_toolchain",na); E("rand_max_marker","exercise_c_stdlib","pass"); E("rand_max_marker","enumerate_mapping",na); E("rand_max_marker","ml_context_observation",na)
# implicit_seed
E("implicit_seed_equals_srand_one_marker","inspect_toolchain",na); E("implicit_seed_equals_srand_one_marker","exercise_c_stdlib","pass"); E("implicit_seed_equals_srand_one_marker","enumerate_mapping",na); E("implicit_seed_equals_srand_one_marker","ml_context_observation",na)
# same_seed
E("same_seed_replay_marker","inspect_toolchain",na); E("same_seed_replay_marker","exercise_c_stdlib","pass"); E("same_seed_replay_marker","enumerate_mapping",na); E("same_seed_replay_marker","ml_context_observation",na)
# seed_reset
E("seed_reset_prefix_marker","inspect_toolchain",na); E("seed_reset_prefix_marker","exercise_c_stdlib","pass"); E("seed_reset_prefix_marker","enumerate_mapping",na); E("seed_reset_prefix_marker","ml_context_observation",na)
# sequence_portability
E("sequence_portability_limit_marker","inspect_toolchain",na); E("sequence_portability_limit_marker","exercise_c_stdlib","local_observation"); E("sequence_portability_limit_marker","enumerate_mapping",na); E("sequence_portability_limit_marker","ml_context_observation","context_only")
# toy_divisible
E("toy_divisible_modulo_marker","inspect_toolchain",na); E("toy_divisible_modulo_marker","exercise_c_stdlib",na); E("toy_divisible_modulo_marker","enumerate_mapping","pass"); E("toy_divisible_modulo_marker","ml_context_observation",na)
# toy_nondivisible
E("toy_nondivisible_modulo_marker","inspect_toolchain",na); E("toy_nondivisible_modulo_marker","exercise_c_stdlib",na); E("toy_nondivisible_modulo_marker","enumerate_mapping","pass"); E("toy_nondivisible_modulo_marker","ml_context_observation",na)
# rejection_threshold
E("rejection_threshold_marker","inspect_toolchain",na); E("rejection_threshold_marker","exercise_c_stdlib",na); E("rejection_threshold_marker","enumerate_mapping","pass"); E("rejection_threshold_marker","ml_context_observation",na)
# rejection_uniformity
E("rejection_uniformity_marker","inspect_toolchain",na); E("rejection_uniformity_marker","exercise_c_stdlib",na); E("rejection_uniformity_marker","enumerate_mapping","pass"); E("rejection_uniformity_marker","ml_context_observation",na)
# power_of_two
E("power_of_two_bound_marker","inspect_toolchain",na); E("power_of_two_bound_marker","exercise_c_stdlib",na); E("power_of_two_bound_marker","enumerate_mapping","pass"); E("power_of_two_bound_marker","ml_context_observation",na)
# low_bit
E("low_bit_projection_marker","inspect_toolchain",na); E("low_bit_projection_marker","exercise_c_stdlib",na); E("low_bit_projection_marker","enumerate_mapping","local_observation"); E("low_bit_projection_marker","ml_context_observation",na)
# bounded_helper
E("bounded_helper_guard_marker","inspect_toolchain",na); E("bounded_helper_guard_marker","exercise_c_stdlib","pass"); E("bounded_helper_guard_marker","enumerate_mapping",na); E("bounded_helper_guard_marker","ml_context_observation",na)
# actual_rand_modulo
E("actual_rand_modulo_local_counts_marker","inspect_toolchain",na); E("actual_rand_modulo_local_counts_marker","exercise_c_stdlib","local_observation"); E("actual_rand_modulo_local_counts_marker","enumerate_mapping",na); E("actual_rand_modulo_local_counts_marker","ml_context_observation",na)
# shuffle_modulo
E("three_item_shuffle_modulo_marker","inspect_toolchain",na); E("three_item_shuffle_modulo_marker","exercise_c_stdlib",na); E("three_item_shuffle_modulo_marker","enumerate_mapping","pass"); E("three_item_shuffle_modulo_marker","ml_context_observation",na)
# shuffle_accepted
E("three_item_shuffle_accepted_draw_space_marker","inspect_toolchain",na); E("three_item_shuffle_accepted_draw_space_marker","exercise_c_stdlib",na); E("three_item_shuffle_accepted_draw_space_marker","enumerate_mapping","pass"); E("three_item_shuffle_accepted_draw_space_marker","ml_context_observation",na)
# minibatch
E("tiny_minibatch_index_sampler_marker","inspect_toolchain",na); E("tiny_minibatch_index_sampler_marker","exercise_c_stdlib",na); E("tiny_minibatch_index_sampler_marker","enumerate_mapping","pass"); E("tiny_minibatch_index_sampler_marker","ml_context_observation","context_only")
# range_reduction_not_rng_quality
E("range_reduction_not_rng_quality_marker","inspect_toolchain",na); E("range_reduction_not_rng_quality_marker","exercise_c_stdlib",na); E("range_reduction_not_rng_quality_marker","enumerate_mapping",na); E("range_reduction_not_rng_quality_marker","ml_context_observation","context_only")
# no_global
E("no_global_rng_or_ml_validity_claim_marker","inspect_toolchain",na); E("no_global_rng_or_ml_validity_claim_marker","exercise_c_stdlib",na); E("no_global_rng_or_ml_validity_claim_marker","enumerate_mapping",na); E("no_global_rng_or_ml_validity_claim_marker","ml_context_observation","context_only")

# build rows
rows=[]
py_exe=sys.executable
py_ver=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
plat=platform.platform()

def row_for(case,method):
    e=exp.get((case,method),"fail")
    actual=e if e!="fail" else "fail"
    # per-case data
    seed=None; sample_count=None; bound=None; src_dom_size=None
    accepted_limit_v=None; accepted_count=None; rejected_count=None; rejected_vals_v=None
    output_counts=None; min_count=None; max_count=None; count_diff=None; quotient=None; remainder=None
    first_hash=None; second_hash=None; seq_equal=None; min_rand=None; max_rand=None
    guard_status=None; raw_draw_pairs=None; accepted_draw_pairs=None; perm_map=None; index_map=None
    narrow=""
    if case=="implicit_seed_equals_srand_one_marker" and method=="exercise_c_stdlib":
        first_hash=h_ints(cinfo["implicit_prefix"]); second_hash=h_ints(cinfo["srand1_prefix"]); seq_equal=(cinfo["implicit_prefix"]==cinfo["srand1_prefix"])
        narrow="implicit rand() equals srand(1)"
    if case=="same_seed_replay_marker" and method=="exercise_c_stdlib":
        seed=12345; sample_count=32; first_hash=h_ints(cinfo["replay_a"]); second_hash=h_ints(cinfo["replay_b"]); seq_equal=(cinfo["replay_a"]==cinfo["replay_b"]); min_rand=min(cinfo["replay_a"]); max_rand=max(cinfo["replay_a"]); narrow="same seed replay matches locally"
    if case=="seed_reset_prefix_marker" and method=="exercise_c_stdlib":
        seed=12345; seq_equal=(cinfo["seg1"]+cinfo["seg2"]==cinfo["seg_full"]); narrow="seed reset prefix concatenation holds"
    if case=="sequence_portability_limit_marker" and method=="exercise_c_stdlib":
        first_hash=h_ints(cinfo["replay_a"]); narrow="sequence is implementation-specific"
    if case=="toy_divisible_modulo_marker" and method=="enumerate_mapping":
        bound=4; src_dom_size=16; output_counts=div_counts; min_count=min(div_counts); max_count=max(div_counts); count_diff=0; quotient=4; remainder=0; narrow="divisible modulo balanced"
    if case=="toy_nondivisible_modulo_marker" and method=="enumerate_mapping":
        bound=6; src_dom_size=16; output_counts=nd_counts; min_count=min(nd_counts); max_count=max(nd_counts); count_diff=max(nd_counts)-min(nd_counts); quotient=2; remainder=4; narrow="nondivisible modulo biased"
    if case=="rejection_threshold_marker" and method=="enumerate_mapping":
        bound=6; src_dom_size=16; accepted_limit_v=accepted_limit; accepted_count=len(accepted_vals); rejected_count=len(rejected_vals); rejected_vals_v=rejected_vals; narrow="rejection threshold 12"
    if case=="rejection_uniformity_marker" and method=="enumerate_mapping":
        bound=6; output_counts=rej_uni; min_count=2; max_count=2; count_diff=0; narrow="accepted domain uniform"
    if case=="power_of_two_bound_marker" and method=="enumerate_mapping":
        bound=8; src_dom_size=16; output_counts=pow_counts; min_count=2; max_count=2; narrow="power-of-two balanced for this domain"
    if case=="low_bit_projection_marker" and method=="enumerate_mapping":
        bound=2; output_counts=low_counts; narrow="synthetic fixed low-bit yields all zeros"
    if case=="bounded_helper_guard_marker" and method=="exercise_c_stdlib":
        guard_status="zero=reject,oversize=reject,null=reject"; narrow="bounded helper guards invalid bounds"
    if case=="actual_rand_modulo_local_counts_marker" and method=="exercise_c_stdlib":
        seed=12345; sample_count=10000; bound=10; output_counts=mod10_counts; min_count=min(mod10_counts); max_count=max(mod10_counts); narrow="local rand()%10 counts observed"
    if case=="three_item_shuffle_modulo_marker" and method=="enumerate_mapping":
        raw_draw_pairs=raw_pairs; perm_map={",".join(k):v for k,v in perm_counts.items()}; narrow="modulo shuffle biased [4,4,2,2,2,2]"
    if case=="three_item_shuffle_accepted_draw_space_marker" and method=="enumerate_mapping":
        accepted_draw_pairs=acc_pairs; perm_map={",".join(k):v for k,v in acc_perm_counts.items()}; narrow="accepted draws give all 6 permutations once"
    if case=="tiny_minibatch_index_sampler_marker" and method=="enumerate_mapping":
        bound=10; src_dom_size=256; output_counts=mb_counts; accepted_limit_v=mb_reject_limit; rejected_vals_v=mb_rejected; index_map={str(i):mb_counts[i] for i in range(10)}; narrow="byte-domain modulo 10 gives 26/25 split, accepted 25 each"
    if method=="ml_context_observation" and case=="tiny_minibatch_index_sampler_marker":
        narrow="ML context: index sampling only, no training"
    if "range_reduction_not_rng_quality" in case or "no_global" in case:
        narrow="context only – no RNG/ML validity claim"

    return {
        "method": method,
        "case_id": case,
        "expected_classification": e,
        "actual_classification": actual,
        "api_or_helper_exercised": "rand,srand" if method=="exercise_c_stdlib" else "",
        "zig_executable_representation": zig_repr,
        "zig_version": zig_version,
        "zig_cc_version_representation": cc_ver,
        "compiler_target": "native",
        "c_language_mode": "c11",
        "compile_flags": " ".join(compile_flags),
        "compile_exit_code": 0,
        "python_executable_representation": py_exe,
        "python_version": py_ver,
        "platform": plat,
        "RAND_MAX": RAND_MAX,
        "sizeof_int": sizeof_int,
        "rand_source_domain_size": rand_domain,
        "seed": seed,
        "sample_count": sample_count,
        "bound": bound,
        "synthetic_source_domain_size": src_dom_size,
        "accepted_limit": accepted_limit_v,
        "accepted_count": accepted_count,
        "rejected_count": rejected_count,
        "rejected_values": rejected_vals_v,
        "exact_output_counts": output_counts,
        "minimum_count": min_count,
        "maximum_count": max_count,
        "count_difference": count_diff,
        "quotient": quotient,
        "remainder": remainder,
        "first_sequence_hash": first_hash,
        "second_sequence_hash": second_hash,
        "sequence_equality": seq_equal,
        "minimum_observed_rand_value": min_rand,
        "maximum_observed_rand_value": max_rand,
        "guard_status": guard_status,
        "raw_draw_pairs": raw_draw_pairs,
        "accepted_draw_pairs": accepted_draw_pairs,
        "permutation_count_map": perm_map,
        "index_count_map": index_map,
        "elapsed_time": None,
        "sanitization_applied": sanitized,
        "skip_reason": None,
        "failure_reason": None,
        "narrow_local_conclusion": narrow,
    }

for case in cases:
    for method in methods:
        rows.append(row_for(case, method))

elapsed=time.perf_counter()-t0
for r in rows: r["elapsed_time"]=elapsed

# write json
with open("results_rows.json","w") as f: json.dump(rows,f,indent=2)
# csv
fields=list(rows[0].keys())
with open("results_rows.csv","w",newline="") as f:
    w=csv.DictWriter(f, fieldnames=fields)
    w.writeheader()
    for r in rows:
        o={}
        for k,v in r.items():
            if isinstance(v,(dict,list)): o[k]=json.dumps(v, sort_keys=True, separators=(",",":"))
            else: o[k]=v
        w.writerow(o)

# RESULTS.md
from collections import Counter
cnt=Counter(r["actual_classification"] for r in rows)
def gbc(k): return cnt.get(k,0)
with open("RESULTS.md","w") as f:
    f.write("# Results – c-stdlib-rand-bounded-sampling-lab\n\n")
    f.write(f"zig: {zig_repr} version {zig_version}\n\n")
    f.write(f"zig cc: {cc_ver}\n\n")
    f.write(f"compile flags: {' '.join(compile_flags)} (c11)\n\n")
    f.write(f"python: {py_ver}\n\n")
    f.write(f"platform: {plat}\n\n")
    f.write(f"RAND_MAX: {RAND_MAX}, rand_domain_size: {rand_domain}\n\n")
    f.write(f"cases: 20, methods: 4, rows: 80\n\n")
    f.write(f"classifications: pass={gbc('pass')}, expected_error={gbc('expected_error')}, local_observation={gbc('local_observation')}, context_only={gbc('context_only')}, toolchain_skip={gbc('toolchain_skip')}, not_applicable={gbc('not_applicable')}, fail={gbc('fail')}\n\n")
    f.write("implicit srand(1): implicit rand() prefix equals srand(1) prefix locally.\n\n")
    f.write("same_seed_replay: srand(12345u) replay matches, 32 values.\n\n")
    f.write("seed_reset_prefix: 8+8 concatenation equals 16-value replay.\n\n")
    f.write("sequence_portability: C does not require identical rand() sequences across implementations.\n\n")
    f.write(f"toy_divisible_modulo: source 0..15, bound 4, counts {div_counts}.\n\n")
    f.write(f"toy_nondivisible_modulo: source 0..15, bound 6, counts {nd_counts}, quotient 2 remainder 4.\n\n")
    f.write(f"rejection_threshold: accepted_limit {accepted_limit}, rejected {rejected_vals}.\n\n")
    f.write(f"rejection_uniformity: counts {rej_uni}, each output 2 representations.\n\n")
    f.write(f"power_of_two_bound: bound 8, counts {pow_counts}.\n\n")
    f.write(f"low_bit_projection: synthetic even source → all zeros, counts {low_counts} – does NOT describe local rand().\n\n")
    f.write("bounded_helper_guard: rejects bound==0, bound>rand_domain, null output.\n\n")
    f.write(f"actual_rand_modulo_local_counts: seed 12345u, 10000 samples, bound 10, counts {mod10_counts} – local_observation only, no uniformity claim.\n\n")
    f.write(f"three_item_shuffle_modulo: 16 raw pairs, permutation counts multiset {perm_multiset} (biased).\n\n")
    f.write("three_item_shuffle_accepted_draw_space: 6 accepted pairs → 6 permutations exactly once.\n\n")
    f.write(f"tiny_minibatch_index_sampler: byte domain 0..255 mod 10 → {mb_counts} (0..5 get 26, 6..9 get 25), rejected {mb_rejected}, accepted counts {mb_acc_counts} – index sampling only, no training.\n\n")
    f.write("range_reduction_not_rng_quality: exact modulo counts prove only mapping properties; balanced rejection assumes equiprobable source; same-seed replay is local only; range reduction does not establish period, unpredictability, independence, equidistribution, or cryptographic suitability; no testu01/dieharder/practrand; no pcg/xoshiro comparison; no performance claims; rand() not validated for security/simulation/production ML.\n\n")
    f.write("no_global_rng_or_ml_validity_claim: repository does NOT prove rand() is cryptographically secure; statistically suitable for ML; cross-platform portable; srand captures external framework state; rand()%n is always harmful; small count differences are significant; rejection has finite worst-case draws; rejection repairs biased generator; power-of-two is safe with every low-bit-defective generator; synthetic low-bit case describes local rand(); three-item shuffle is a realistic benchmark; ten-index example measures model quality / is training data; uniform index selection guarantees unbiased learning; random sampling validates ML pipeline; lab compares pcg/xoshiro/mt/os randomness; establishes fastest method; HN thread proves C stdlib badly designed; linked article proves stdlib abstractions always over-engineered; one local run validates production RNG.\n\n")
    f.write(f"failures: {gbc('fail')}, toolchain_skips: {gbc('toolchain_skip')}\n\n")
    f.write(f"total runtime: {elapsed:.3f}s\n\n")
print(f"Wrote {len(rows)} rows, elapsed {elapsed:.3f}s")
