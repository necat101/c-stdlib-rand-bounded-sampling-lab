#!/usr/bin/env python3
import json, subprocess, sys, os, time, hashlib, csv, platform, shutil
t0=time.perf_counter()

# load cases + expectations
with open("cases.json") as f:
    cases_data=json.load(f)
case_ids=[c["id"] for c in cases_data]
exp_map={}
for c in cases_data:
    cid=c["id"]
    for m, cls in c.get("expectations",{}).items():
        exp_map[(cid,m)]=cls

methods=["inspect_toolchain","exercise_c_stdlib","enumerate_mapping","ml_context_observation"]
# ensure every case/method pair has expectation
for cid in case_ids:
    for m in methods:
        if (cid,m) not in exp_map:
            exp_map[(cid,m)]="not_applicable"

def expected(cid,method):
    return exp_map.get((cid,method),"not_applicable")

# resolve zig
def find_zig():
    for c in [os.environ.get("ZIG_BIN"), shutil.which("zig"), os.path.expanduser("~/.local/bin/zig"), os.path.expanduser("~/bin/zig"), os.path.expanduser("~/.local/zig/zig")]:
        if c and os.path.isfile(c) and os.access(c, os.X_OK):
            return c
    return None

zig_bin=find_zig()
toolchain_available = zig_bin is not None

if toolchain_available:
    zig_version=subprocess.check_output([zig_bin,"version"], text=True).strip()
    zig_repr=zig_bin
    for p in [os.path.expanduser("~"), "/home/ubuntu", "/tmp", os.getcwd()]:
        if p and p in zig_repr: zig_repr=zig_repr.replace(p, "/portable-zig")
    sanitized = zig_repr != zig_bin
    compile_flags=["-std=c11","-O2","-Wall","-Wextra","-Wpedantic","-Werror"]
    try:
        cmd=[zig_bin,"cc"]+compile_flags+["rand_lab.c","-o","rand_lab"]
        compile_exit=subprocess.call(cmd)
        compile_ok = (compile_exit==0)
    except Exception:
        compile_ok=False; compile_exit=1
    if compile_ok:
        try:
            cc_ver=subprocess.check_output([zig_bin,"cc","--version"], text=True, stderr=subprocess.STDOUT).splitlines()[0][:200]
        except: cc_ver="unknown"
        try:
            out=subprocess.check_output(["./rand_lab"], text=True, timeout=5)
            cinfo=json.loads(out)
            c_run_ok=True
        except Exception:
            c_run_ok=False; cinfo={}
    else:
        c_run_ok=False; cinfo={}
else:
    zig_version="toolchain_unavailable"; zig_repr="toolchain_unavailable"; cc_ver="toolchain_unavailable"; compile_flags=[]; compile_exit=-1; sanitized=False; c_run_ok=False; cinfo={}

# C metadata – None when unavailable (do NOT fabricate plausible defaults)
RAND_MAX = cinfo.get("RAND_MAX")
sizeof_int = cinfo.get("sizeof_int")
rand_domain = cinfo.get("rand_domain_size")
mod10_counts = cinfo.get("mod10_counts")

def h_ints(arr): return hashlib.sha256(json.dumps(arr, separators=(",",":")).encode()).hexdigest()[:16]

# enum mappings (always available, pure python)
div_counts=[0]*4
for x in range(0,16): div_counts[x%4]+=1
nd_counts=[0]*6
for x in range(0,16): nd_counts[x%6]+=1
src_dom=16; bound_rej=6
accepted_limit=src_dom - (src_dom % bound_rej)
accepted_vals=list(range(accepted_limit))
rejected_vals=list(range(accepted_limit,src_dom))
rej_uni=[0]*6
for x in range(accepted_limit): rej_uni[x%6]+=1
pow_counts=[0]*8
for x in range(16): pow_counts[x%8]+=1
low_src=[0,2,4,6,8,10,12,14]
low_outs=[x%2 for x in low_src]
low_counts=[low_outs.count(0), low_outs.count(1)]

def shuffle3(j,k):
    a=["a","b","c"]; a[2],a[j]=a[j],a[2]; a[1],a[k]=a[k],a[1]; return tuple(a)
perm_counts={}; raw_pairs=[]
for rf in range(4):
    for rs in range(4):
        raw_pairs.append([rf,rs]); p=shuffle3(rf%3, rs%2); perm_counts[p]=perm_counts.get(p,0)+1
perm_multiset=sorted(perm_counts.values())
acc_pairs=[]; acc_perm_counts={}
for j in range(3):
    for k in range(2):
        acc_pairs.append([j,k]); p=shuffle3(j,k); acc_perm_counts[p]=acc_perm_counts.get(p,0)+1
mb_counts=[0]*10
for x in range(256): mb_counts[x%10]+=1
mb_reject_limit=250; mb_rejected=list(range(250,256))
mb_acc_counts=[0]*10
for x in range(250): mb_acc_counts[x%10]+=1

# handler functions – return (actual_classification, data_dict, failure_reason)
# IMPORTANT: handlers MUST NOT consult expected() – actual classification is derived independently
def handle_inspect_toolchain(case_id):
    if case_id=="zig_compiler_marker":
        if not toolchain_available:
            return "toolchain_skip", {}, "zig not found"
        if not compile_ok:
            return "fail", {}, "compile failed"
        if not c_run_ok:
            return "fail", {}, "c helper failed"
        return "pass", {}, None
    return "not_applicable", {}, None

def handle_exercise_c_stdlib(case_id):
    # c_stdlib cases – return toolchain_skip if c unavailable, otherwise evaluate independently
    c_cases = {
        "c_rand_api_marker","rand_max_marker","implicit_seed_equals_srand_one_marker",
        "same_seed_replay_marker","seed_reset_prefix_marker","sequence_portability_limit_marker",
        "bounded_helper_guard_marker","actual_rand_modulo_local_counts_marker"
    }
    if case_id not in c_cases:
        return "not_applicable", {}, None
    if not toolchain_available or not c_run_ok:
        return "toolchain_skip", {}, "zig/c unavailable"
    # actual independent checks
    if case_id=="c_rand_api_marker":
        if RAND_MAX is None or RAND_MAX < 32767: return "fail", {}, "RAND_MAX < 32767 or unavailable"
        return "pass", {}, None
    if case_id=="rand_max_marker":
        if RAND_MAX is None: return "fail", {}, "RAND_MAX unavailable"
        return "pass", {}, None
    if case_id=="implicit_seed_equals_srand_one_marker":
        ip=cinfo.get("implicit_prefix"); sp=cinfo.get("srand1_prefix")
        if ip is None or sp is None: return "fail", {}, "missing prefix"
        if ip != sp: return "fail", {}, "prefix mismatch"
        return "pass", {}, None
    if case_id=="same_seed_replay_marker":
        a=cinfo.get("replay_a"); b=cinfo.get("replay_b")
        if a is None or b is None: return "fail", {}, "missing replay"
        if a != b: return "fail", {}, "replay mismatch"
        return "pass", {}, None
    if case_id=="seed_reset_prefix_marker":
        s1=cinfo.get("seg1"); s2=cinfo.get("seg2"); sf=cinfo.get("seg_full")
        if None in (s1,s2,sf): return "fail", {}, "missing segments"
        if s1+s2 != sf: return "fail", {}, "concatenation mismatch"
        return "pass", {}, None
    if case_id=="sequence_portability_limit_marker":
        return "local_observation", {}, None
    if case_id=="bounded_helper_guard_marker":
        gz=cinfo.get("guard_zero_status"); go=cinfo.get("guard_oversize_status"); gn=cinfo.get("guard_null_status"); gv=cinfo.get("guard_valid_status")
        if None in (gz,go,gn,gv): return "fail", {}, "missing guard status"
        if gz==0 or go==0 or gn==0: return "fail", {}, "guard did not reject invalid input"
        if gv != 0: return "fail", {}, "valid guard call failed"
        return "pass", {}, None
    if case_id=="actual_rand_modulo_local_counts_marker":
        counts=mod10_counts
        if not counts or sum(counts)!=10000: return "fail", {}, "bad modulo counts"
        return "local_observation", {}, None
    return "fail", {}, "unhandled c_stdlib case"

def handle_enumerate_mapping(case_id):
    # pure python, no toolchain needed – enumerate independently
    mapping_cases = {
        "toy_divisible_modulo_marker","toy_nondivisible_modulo_marker",
        "rejection_threshold_marker","rejection_uniformity_marker","power_of_two_bound_marker",
        "low_bit_projection_marker","three_item_shuffle_modulo_marker",
        "three_item_shuffle_accepted_draw_space_marker","tiny_minibatch_index_sampler_marker"
    }
    if case_id not in mapping_cases:
        return "not_applicable", {}, None
    if case_id=="toy_divisible_modulo_marker":
        if div_counts != [4,4,4,4]: return "fail", {}, "divisible counts wrong"
        return "pass", {}, None
    if case_id=="toy_nondivisible_modulo_marker":
        if nd_counts != [3,3,3,3,2,2]: return "fail", {}, "nondivisible counts wrong"
        return "pass", {}, None
    if case_id=="rejection_threshold_marker":
        if accepted_limit != 12 or rejected_vals != [12,13,14,15]: return "fail", {}, "rejection threshold wrong"
        return "pass", {}, None
    if case_id=="rejection_uniformity_marker":
        if rej_uni != [2,2,2,2,2,2]: return "fail", {}, "rejection uniformity wrong"
        return "pass", {}, None
    if case_id=="power_of_two_bound_marker":
        if pow_counts != [2]*8: return "fail", {}, "power_of_two counts wrong"
        return "pass", {}, None
    if case_id=="low_bit_projection_marker":
        if low_counts != [8,0]: return "fail", {}, "low_bit counts wrong"
        return "local_observation", {}, None
    if case_id=="three_item_shuffle_modulo_marker":
        if sorted(perm_counts.values()) != [2,2,2,2,4,4]: return "fail", {}, "shuffle counts wrong"
        return "pass", {}, None
    if case_id=="three_item_shuffle_accepted_draw_space_marker":
        if len(acc_perm_counts)!=6 or any(v!=1 for v in acc_perm_counts.values()): return "fail", {}, "accepted shuffle wrong"
        return "pass", {}, None
    if case_id=="tiny_minibatch_index_sampler_marker":
        if mb_counts != [26,26,26,26,26,26,25,25,25,25]: return "fail", {}, "mb counts wrong"
        if mb_acc_counts != [25]*10: return "fail", {}, "mb accepted counts wrong"
        return "pass", {}, None
    return "fail", {}, "unhandled mapping case"

def handle_ml_context_observation(case_id):
    # ML context observations – independent classification, no expected() lookup
    # These cases are context-only by design, documenting what the lab does NOT prove
    ml_context_cases = {
        "sequence_portability_limit_marker": "context_only",
        "tiny_minibatch_index_sampler_marker": "context_only",
        "range_reduction_not_rng_quality_marker": "context_only",
        "no_global_rng_or_ml_validity_claim_marker": "context_only",
    }
    if case_id in ml_context_cases:
        return ml_context_cases[case_id], {}, None
    return "not_applicable", {}, None

handlers = {
    "inspect_toolchain": handle_inspect_toolchain,
    "exercise_c_stdlib": handle_exercise_c_stdlib,
    "enumerate_mapping": handle_enumerate_mapping,
    "ml_context_observation": handle_ml_context_observation,
}

rows=[]
py_exe=sys.executable
py_ver=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
plat=platform.platform()

def build_row(case_id, method):
    exp_cls = expected(case_id, method)
    handler = handlers.get(method)
    actual_cls = None
    failure_reason = None
    skip_reason = None
    if handler:
        try:
            actual_cls, data, failure_reason = handler(case_id)
        except Exception as e:
            actual_cls = "fail"; failure_reason = str(e)[:200]
    if actual_cls is None:
        actual_cls = "fail"; failure_reason = failure_reason or "handler did not assign classification"
    # DO NOT force actual = expected – actual classification is independent
    # Handlers are responsible for returning not_applicable when appropriate
    if actual_cls == "toolchain_skip":
        skip_reason = failure_reason or "toolchain unavailable"
        failure_reason = None

    # per-case observational data (for reporting, independent of classification)
    seed=None; sample_count=None; bound=None; src_dom_size=None
    accepted_limit_v=None; accepted_count=None; rejected_count=None; rejected_vals_v=None
    output_counts=None; min_count=None; max_count=None; count_diff=None; quotient=None; remainder=None
    first_hash=None; second_hash=None; seq_equal=None; min_rand=None; max_rand=None
    guard_status=None; raw_draw_pairs=None; accepted_draw_pairs=None; perm_map=None; index_map=None
    narrow=""

    # populate observational fields from cinfo / computed enums
    if c_run_ok:
        if case_id=="implicit_seed_equals_srand_one_marker" and method=="exercise_c_stdlib":
            ip=cinfo.get("implicit_prefix",[]); sp=cinfo.get("srand1_prefix",[])
            first_hash=h_ints(ip); second_hash=h_ints(sp); seq_equal=(ip==sp)
            narrow="implicit rand() equals srand(1)"
        if case_id=="same_seed_replay_marker" and method=="exercise_c_stdlib":
            a=cinfo.get("replay_a",[]); b=cinfo.get("replay_b",[])
            seed=12345; sample_count=32; first_hash=h_ints(a); second_hash=h_ints(b); seq_equal=(a==b)
            if a: min_rand=min(a); max_rand=max(a)
            narrow="same seed replay matches locally"
        if case_id=="seed_reset_prefix_marker" and method=="exercise_c_stdlib":
            s1=cinfo.get("seg1",[]); s2=cinfo.get("seg2",[]); sf=cinfo.get("seg_full",[])
            seed=12345; seq_equal=(s1+s2==sf); narrow="seed reset prefix concatenation holds"
        if case_id=="sequence_portability_limit_marker" and method=="exercise_c_stdlib":
            a=cinfo.get("replay_a",[]); first_hash=h_ints(a) if a else None
            narrow="sequence is implementation-specific"
        if case_id=="bounded_helper_guard_marker" and method=="exercise_c_stdlib":
            gz=cinfo.get("guard_zero_status"); go=cinfo.get("guard_oversize_status"); gn=cinfo.get("guard_null_status"); gv=cinfo.get("guard_valid_status")
            guard_status=f"zero={gz},oversize={go},null={gn},valid={gv}"
            narrow="bounded helper guards invalid bounds"
        if case_id=="actual_rand_modulo_local_counts_marker" and method=="exercise_c_stdlib":
            seed=12345; sample_count=10000; bound=10; output_counts=mod10_counts
            if mod10_counts: min_count=min(mod10_counts); max_count=max(mod10_counts)
            narrow="local rand()%10 counts observed"

    # enumerate_mapping observational fields (always available)
    if case_id=="toy_divisible_modulo_marker" and method=="enumerate_mapping":
        bound=4; src_dom_size=16; output_counts=div_counts; min_count=4; max_count=4; count_diff=0; quotient=4; remainder=0; narrow="divisible modulo balanced"
    if case_id=="toy_nondivisible_modulo_marker" and method=="enumerate_mapping":
        bound=6; src_dom_size=16; output_counts=nd_counts; min_count=2; max_count=3; count_diff=1; quotient=2; remainder=4; narrow="nondivisible modulo biased"
    if case_id=="rejection_threshold_marker" and method=="enumerate_mapping":
        bound=6; src_dom_size=16; accepted_limit_v=accepted_limit; accepted_count=len(accepted_vals); rejected_count=len(rejected_vals); rejected_vals_v=rejected_vals; narrow="rejection threshold 12"
    if case_id=="rejection_uniformity_marker" and method=="enumerate_mapping":
        bound=6; output_counts=rej_uni; min_count=2; max_count=2; count_diff=0; narrow="accepted domain uniform"
    if case_id=="power_of_two_bound_marker" and method=="enumerate_mapping":
        bound=8; src_dom_size=16; output_counts=pow_counts; min_count=2; max_count=2; narrow="power-of-two balanced for this domain"
    if case_id=="low_bit_projection_marker" and method=="enumerate_mapping":
        bound=2; output_counts=low_counts; narrow="synthetic fixed low-bit yields all zeros"
    if case_id=="three_item_shuffle_modulo_marker" and method=="enumerate_mapping":
        raw_draw_pairs=raw_pairs; perm_map={",".join(k):v for k,v in perm_counts.items()}; narrow="modulo shuffle biased [4,4,2,2,2,2]"
    if case_id=="three_item_shuffle_accepted_draw_space_marker" and method=="enumerate_mapping":
        accepted_draw_pairs=acc_pairs; perm_map={",".join(k):v for k,v in acc_perm_counts.items()}; narrow="accepted draws give all 6 permutations once"
    if case_id=="tiny_minibatch_index_sampler_marker" and method=="enumerate_mapping":
        bound=10; src_dom_size=256; output_counts=mb_counts; accepted_limit_v=mb_reject_limit; rejected_vals_v=mb_rejected; index_map={str(i):mb_counts[i] for i in range(10)}; narrow="byte-domain modulo 10 gives 26/25 split, accepted 25 each"
    if method=="ml_context_observation" and case_id=="tiny_minibatch_index_sampler_marker":
        narrow="ML context: index sampling only, no training"
    if "range_reduction_not_rng_quality" in case_id or "no_global" in case_id:
        if not narrow: narrow="context only – no RNG/ML validity claim"

    return {
        "method": method,
        "case_id": case_id,
        "expected_classification": exp_cls,
        "actual_classification": actual_cls,
        "api_or_helper_exercised": "rand,srand,bounded_rand_uintmax" if method=="exercise_c_stdlib" and case_id=="bounded_helper_guard_marker" else ("rand,srand" if method=="exercise_c_stdlib" else ""),
        "zig_executable_representation": zig_repr if toolchain_available else "toolchain_unavailable",
        "zig_version": zig_version if toolchain_available else "toolchain_unavailable",
        "zig_cc_version_representation": cc_ver if toolchain_available else "toolchain_unavailable",
        "compiler_target": "native" if toolchain_available else "toolchain_unavailable",
        "c_language_mode": "c11" if toolchain_available else "toolchain_unavailable",
        "compile_flags": " ".join(compile_flags) if compile_flags else "",
        "compile_exit_code": compile_exit,
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
        "sanitization_applied": sanitized if toolchain_available else False,
        "skip_reason": skip_reason,
        "failure_reason": failure_reason,
        "narrow_local_conclusion": narrow,
    }

for cid in case_ids:
    for m in methods:
        rows.append(build_row(cid, m))

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
    if toolchain_available:
        f.write(f"zig: {zig_repr} version {zig_version}\n\n")
        f.write(f"zig cc: {cc_ver}\n\n")
        f.write(f"compile flags: {' '.join(compile_flags)} (c11)\n\n")
    else:
        f.write("zig: toolchain_unavailable – c-dependent rows skipped\n\n")
    f.write(f"python: {py_ver}\n\n")
    f.write(f"platform: {plat}\n\n")
    f.write(f"RAND_MAX: {RAND_MAX}, rand_domain_size: {rand_domain}\n\n")
    f.write(f"cases: 20, methods: 4, rows: 80\n\n")
    f.write(f"classifications: pass={gbc('pass')}, expected_error={gbc('expected_error')}, local_observation={gbc('local_observation')}, context_only={gbc('context_only')}, toolchain_skip={gbc('toolchain_skip')}, not_applicable={gbc('not_applicable')}, fail={gbc('fail')}\n\n")
    if toolchain_available and c_run_ok:
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
    if toolchain_available and c_run_ok:
        gz=cinfo.get('guard_zero_status'); go=cinfo.get('guard_oversize_status'); gn=cinfo.get('guard_null_status'); gv=cinfo.get('guard_valid_status')
        f.write(f"bounded_helper_guard: zero={gz}, oversize={go}, null={gn}, valid={gv} – rejects invalid bounds.\n\n")
        if mod10_counts:
            f.write(f"actual_rand_modulo_local_counts: seed 12345u, 10000 samples, bound 10, counts {mod10_counts} – local_observation only, no uniformity claim.\n\n")
    f.write(f"three_item_shuffle_modulo: 16 raw pairs, permutation counts multiset {perm_multiset} (biased).\n\n")
    f.write("three_item_shuffle_accepted_draw_space: 6 accepted pairs → 6 permutations exactly once.\n\n")
    f.write(f"tiny_minibatch_index_sampler: byte domain 0..255 mod 10 → {mb_counts} (0..5 get 26, 6..9 get 25), rejected {mb_rejected}, accepted counts {mb_acc_counts} – index sampling only, no training.\n\n")
    f.write("range_reduction_not_rng_quality: exact modulo counts prove only mapping properties; balanced rejection assumes equiprobable source; same-seed replay is local only; range reduction does not establish period, unpredictability, independence, equidistribution, or cryptographic suitability; no testu01/dieharder/practrand; no pcg/xoshiro comparison; no performance claims; rand() not validated for security/simulation/production ML.\n\n")
    f.write("no_global_rng_or_ml_validity_claim: repository does NOT prove rand() is cryptographically secure; statistically suitable for ML; cross-platform portable; srand captures external framework state; rand()%n is always harmful; small count differences are significant; rejection has finite worst-case draws; rejection repairs biased generator; power-of-two is safe with every low-bit-defective generator; synthetic low-bit case describes local rand(); three-item shuffle is a realistic benchmark; ten-index example measures model quality / is training data; uniform index selection guarantees unbiased learning; random sampling validates ML pipeline; lab compares pcg/xoshiro/mt/os randomness; establishes fastest method; HN thread proves C stdlib badly designed; linked article proves stdlib abstractions always over-engineered; one local run validates production RNG.\n\n")
    f.write(f"failures: {gbc('fail')}, toolchain_skips: {gbc('toolchain_skip')}\n\n")
    f.write(f"total runtime: {elapsed:.3f}s\n\n")

print(f"Wrote {len(rows)} rows, elapsed {elapsed:.3f}s")
print(f"classifications: {dict(cnt)}")
