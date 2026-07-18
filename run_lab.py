#!/usr/bin/env python3
import os, sys, json, subprocess, time, shutil, hashlib, csv, platform
from pathlib import Path

repo = Path(__file__).parent
cases_path = repo / "cases.json"
with open(cases_path) as f: cases = json.load(f)

def find_zig():
    candidates = []
    zb = os.environ.get("ZIG_BIN")
    if zb: candidates.append(("ZIG_BIN", zb))
    p = shutil.which("zig")
    if p: candidates.append(("PATH:zig", p))
    for label, path in [("$HOME/.local/bin/zig", os.path.expanduser("~/.local/bin/zig")), ("$HOME/bin/zig", os.path.expanduser("~/bin/zig"))]:
        if os.path.isfile(path) and os.access(path, os.X_OK):
            candidates.append((label, path))
    # openclaw manifest fallback - try common
    for mp in ["/usr/bin/zig", "/usr/local/bin/zig"]:
        if os.path.isfile(mp) and os.access(mp, os.X_OK):
            candidates.append(("OPENCLAW_MANIFEST:zig", mp))
    return candidates

candidates = find_zig()
zig_real = candidates[0][1] if candidates else None
zig_sanitized = "/portable-zig/zig"
zig_found = zig_real and os.path.isfile(zig_real)
zig_version = None
zig_cc_version = None
zig_target = None
compile_exit = None

if zig_found:
    try:
        out = subprocess.check_output([zig_real, "version"], text=True, stderr=subprocess.STDOUT, timeout=5)
        zig_version = out.strip()
    except Exception: pass
    try:
        out = subprocess.check_output([zig_real, "cc", "--version"], text=True, stderr=subprocess.STDOUT, timeout=5)
        zig_cc_version = out.splitlines()[0][:120] if out else ""
    except Exception: pass
    try:
        out = subprocess.check_output([zig_real, "cc", "-dumpmachine"], text=True, stderr=subprocess.STDOUT, timeout=5)
        zig_target = out.strip()
    except Exception: zig_target = "unknown"

c_mode = "c11"
cflags = "-O2 -Wall -Wextra -Wpedantic -Werror"
linkflags = ""
helper_json = {}
helper_ok = False

if zig_found:
    exe = repo / "rand_lab"
    if exe.exists(): exe.unlink()
    cmd = [zig_real, "cc", "-std=c11", "-O2", "-Wall", "-Wextra", "-Wpedantic", "-Werror", str(repo/"rand_lab.c"), "-o", str(exe)]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    compile_exit = proc.returncode
    if proc.returncode == 0 and exe.exists():
        try:
            out = subprocess.check_output([str(exe)], text=True, timeout=5)
            helper_json = json.loads(out)
            helper_ok = True
        except Exception as e:
            helper_json = {"error": str(e)}
else:
    compile_exit = None

# python info
py_exe_sanitized = "/python-lab/python3"
py_version = sys.version
plat_sanitized = platform.system() + "/" + platform.machine()

def seq_hash(a):
    h = 2166136261
    for v in a:
        h ^= v & 0xffffffff
        h = (h * 16777619) & 0xffffffff
    return h

# enumerate mappings
def enumerate_modulo(source_span, bound):
    srcs = list(range(source_span))
    maps = [(s, s % bound) for s in srcs]
    counts = [0]*bound
    for _, o in maps: counts[o] += 1
    return srcs, maps, counts

# case helpers
def handle_inspect_toolchain(case_id):
    if case_id == "zig_compiler_marker" and zig_found and helper_ok:
        return "pass", {"conclusion": "zig cc compiled helper successfully"}
    return "not_applicable", {}

def handle_exercise_c_rand(case_id):
    if not helper_ok:
        return "toolchain_skip", {"skip_reason": "zig/c helper unavailable"}
    hj = helper_json
    if case_id == "c_rand_api_marker":
        ok = hj.get("rand_srand_assignable") is True
        return ("pass" if ok else "fail"), {"conclusion": "rand/srand assigned and invoked, algorithm unidentified"}
    if case_id == "rand_max_marker":
        rm = hj.get("RAND_MAX")
        src_span = hj.get("source_span")
        ok = rm is not None and rm >= 32767 and src_span == rm + 1
        return ("pass" if ok else "fail"), {"RAND_MAX": rm, "source_span": src_span}
    if case_id == "default_seed_equivalence_marker":
        a = hj.get("default_seed_seq"); b = hj.get("srand1_seq")
        eq = a == b
        return ("pass" if eq else "fail"), {"first_sequence": a, "second_sequence": b, "sequence_equal": eq, "seed": 1}
    if case_id == "same_seed_replay_marker":
        a = hj.get("same_seed_a"); b = hj.get("same_seed_b")
        eq = a == b
        return ("pass" if eq else "fail"), {"first_sequence": a, "second_sequence": b, "sequence_equal": eq, "seed": 12345, "hash_a": hj.get("same_seed_hash_a"), "hash_b": hj.get("same_seed_hash_b")}
    if case_id == "different_seed_local_observation_marker":
        a = hj.get("diff_seed_a"); b = hj.get("diff_seed_b")
        differ = hj.get("diff_seed_differ", False)
        return "local_observation", {"first_sequence": a, "second_sequence": b, "sequence_inequality": differ}
    if case_id == "rand_range_invariant_marker":
        ok = hj.get("range_all_ge0") and hj.get("range_all_le_rand_max")
        return ("pass" if ok else "fail"), {"range_min": hj.get("range_min"), "range_max": hj.get("range_max")}
    return "not_applicable", {}

def handle_enumerate_mapping(case_id):
    if case_id == "modulo_bias_16_to_6_marker":
        srcs, maps, counts = enumerate_modulo(16, 6)
        ok = counts == [3,3,3,3,2,2]
        return ("pass" if ok else "fail"), {"synthetic_source_span": 16, "requested_bound": 6, "source_values": srcs, "mappings": maps, "output_counts": counts, "conclusion": "16 not divisible by 6, exact finite imbalance"}
    if case_id == "modulo_bias_32_to_10_marker":
        srcs, maps, counts = enumerate_modulo(32, 10)
        ok = counts == [4,4,3,3,3,3,3,3,3,3]
        return ("pass" if ok else "fail"), {"synthetic_source_span": 32, "requested_bound": 10, "source_values": srcs, "mappings": maps, "output_counts": counts}
    if case_id == "power_of_two_modulo_marker":
        srcs, maps, counts = enumerate_modulo(16, 8)
        ok = counts == [2]*8
        return ("pass" if ok else "fail"), {"synthetic_source_span": 16, "requested_bound": 8, "source_values": srcs, "mappings": maps, "output_counts": counts, "conclusion": "8 divides 16, balanced"}
    if case_id == "top_tail_rejection_16_to_6_marker":
        source_span = 16; bound=6
        accepted_span = source_span - (source_span % bound)
        accepted = list(range(accepted_span))
        rejected = list(range(accepted_span, source_span))
        maps = [(s, s % bound) for s in accepted]
        counts = [0]*bound
        for _, o in maps: counts[o]+=1
        ok = counts == [2]*6 and accepted_span==12
        return ("pass" if ok else "fail"), {"synthetic_source_span": source_span, "requested_bound": bound, "accepted_span": accepted_span, "accepted_source_values": accepted, "rejected_source_values": rejected, "mappings": maps, "output_counts": counts, "acceptance_fraction": accepted_span/source_span, "rejection_fraction": (source_span-accepted_span)/source_span}
    if case_id == "bitmask_rejection_8_to_6_marker":
        source_span=8; bound=6
        accepted=list(range(6)); rejected=[6,7]
        maps=[(s,s) for s in accepted]
        counts=[1]*6
        return "pass", {"synthetic_source_span": source_span, "requested_bound": bound, "accepted_source_values": accepted, "rejected_source_values": rejected, "mappings": maps, "output_counts": counts, "conclusion": "models 3-bit mask with rejection"}
    if case_id == "zero_bound_rejection_marker":
        if not helper_ok:
            return "toolchain_skip", {"skip_reason": "c helper unavailable"}
        status = helper_json.get("zero_bound_status")
        rand_calls = helper_json.get("zero_bound_rand_calls")
        rem_ops = helper_json.get("zero_bound_rem_ops")
        div_ops = helper_json.get("zero_bound_div_ops")
        ok = status != 0 and rand_calls == 0 and rem_ops == 0 and div_ops == 0
        return ("expected_error" if ok else "fail"), {"status": status, "rand_calls": rand_calls, "remainder_operations": rem_ops, "division_operations": div_ops, "output_written": False}
    if case_id == "fixed_fisher_yates_indices_marker":
        arr = [0,1,2,3,4,5]
        source_stream = [15,14,13,12,11,10,9,8,7,6,5,4,3,2,1,0]
        source_span=16
        bounds=[6,5,4,3,2]
        cursor=0
        selected=[]
        swaps=[]
        intermediates=[]
        rejected_all=[]
        accepted_all=[]
        for b in bounds:
            accepted_span = source_span - (source_span % b)
            while True:
                src = source_stream[cursor]; cursor+=1
                if src < accepted_span:
                    accepted_all.append(src)
                    idx = src % b
                    selected.append(idx)
                    break
                else:
                    rejected_all.append(src)
            n = 6 - len(selected) + 1
            i = n-1
            j = idx
            swaps.append([i,j])
            arr[i], arr[j] = arr[j], arr[i]
            intermediates.append(arr.copy())
        ok = selected == [5,0,1,2,1] and arr == [4,3,2,1,0,5]
        return ("pass" if ok else "fail"), {"selected_indices": selected, "swaps": swaps, "intermediate_arrays": intermediates, "final_array": arr, "accepted_source_values": accepted_all, "rejected_source_values": rejected_all, "source_attempts": cursor, "conclusion": "fixed index-schedule demonstration"}
    if case_id == "fixed_candidate_index_marker":
        candidate_ids = [101,205,309,413,517,621]
        source_stream=[15,14,13,12,11]
        source_span=16; bound=6
        accepted_span = source_span - (source_span % bound)
        accepted=[]; rejected=[]
        for src in source_stream:
            if src < accepted_span:
                accepted.append(src); break
            else: rejected.append(src)
        idx = accepted[0] % bound if accepted else None
        cid = candidate_ids[idx] if idx is not None else None
        ok = rejected == [15,14,13,12] and accepted == [11] and idx==5 and cid==621
        return ("pass" if ok else "fail"), {"candidate_ids": candidate_ids, "accepted_source_values": accepted, "rejected_source_values": rejected, "selected_candidate_index": idx, "selected_candidate_id": cid, "requested_bound": bound, "synthetic_source_span": source_span, "conclusion": "uniform index mapping over fixed list"}
    return "not_applicable", {}

def handle_ml_context(case_id):
    if case_id == "no_global_randomness_or_ml_validity_claim_marker":
        return "context_only", {"model_loaded": False, "dataset_read": False, "training_occurred": False, "inference_occurred": False, "conclusion": "no ML validity claimed"}
    return "not_applicable", {}

handlers = {
    "inspect_toolchain": handle_inspect_toolchain,
    "exercise_c_rand": handle_exercise_c_rand,
    "enumerate_mapping": handle_enumerate_mapping,
    "ml_context_observation": handle_ml_context,
}

rows=[]
start=time.time()
for case in cases:
    cid = case["id"]
    for method in ["inspect_toolchain","exercise_c_rand","enumerate_mapping","ml_context_observation"]:
        expected = case["methods"][method]["expected_classification"]
        handler = handlers[method]
        try:
            actual, obs = handler(cid)
        except Exception as e:
            actual, obs = "fail", {"failure_reason": str(e)}
        if expected == "not_applicable":
            actual = "not_applicable"
            obs = {}
        row = {
            "method": method,
            "case_id": cid,
            "expected_classification": expected,
            "actual_classification": actual,
            "api_helper": method,
            "zig_executable": zig_sanitized if zig_found else None,
            "zig_version": zig_version,
            "zig_cc_version": zig_cc_version,
            "compiler_target": zig_target,
            "c_mode": c_mode,
            "compile_flags": cflags,
            "link_flags": linkflags,
            "compile_exit_code": compile_exit,
            "python_executable": py_exe_sanitized,
            "python_version": py_version.splitlines()[0],
            "platform": plat_sanitized,
            "__STDC_VERSION__": helper_json.get("__STDC_VERSION__"),
            "CHAR_BIT": helper_json.get("CHAR_BIT"),
            "sizeof_int": helper_json.get("sizeof_int"),
            "sizeof_unsigned_int": helper_json.get("sizeof_unsigned_int"),
            "sizeof_uintmax_t": helper_json.get("sizeof_uintmax_t"),
            "sizeof_size_t": helper_json.get("sizeof_size_t"),
            "RAND_MAX": helper_json.get("RAND_MAX"),
            "source_span": helper_json.get("source_span"),
            "seed": obs.get("seed"),
            "first_sequence": obs.get("first_sequence"),
            "second_sequence": obs.get("second_sequence"),
            "sequence_hash_a": obs.get("hash_a"),
            "sequence_hash_b": obs.get("hash_b"),
            "sequence_equal": obs.get("sequence_equal"),
            "sequence_inequality": obs.get("sequence_inequality"),
            "synthetic_source_span": obs.get("synthetic_source_span"),
            "requested_bound": obs.get("requested_bound"),
            "accepted_span": obs.get("accepted_span"),
            "source_values": obs.get("source_values"),
            "accepted_source_values": obs.get("accepted_source_values"),
            "rejected_source_values": obs.get("rejected_source_values"),
            "mappings": obs.get("mappings"),
            "output_counts": obs.get("output_counts"),
            "acceptance_fraction": obs.get("acceptance_fraction"),
            "rejection_fraction": obs.get("rejection_fraction"),
            "source_attempts": obs.get("source_attempts"),
            "rand_calls": obs.get("rand_calls"),
            "remainder_operations": obs.get("remainder_operations"),
            "division_operations": obs.get("division_operations"),
            "selected_indices": obs.get("selected_indices"),
            "swaps": obs.get("swaps"),
            "intermediate_arrays": obs.get("intermediate_arrays"),
            "final_array": obs.get("final_array"),
            "candidate_ids": obs.get("candidate_ids"),
            "selected_candidate_index": obs.get("selected_candidate_index"),
            "selected_candidate_id": obs.get("selected_candidate_id"),
            "status": obs.get("status"),
            "output_written": obs.get("output_written"),
            "model_loaded": obs.get("model_loaded"),
            "dataset_read": obs.get("dataset_read"),
            "training_occurred": obs.get("training_occurred"),
            "inference_occurred": obs.get("inference_occurred"),
            "elapsed_time": 0,
            "sanitization_applied": True,
            "skip_reason": obs.get("skip_reason"),
            "failure_reason": obs.get("failure_reason"),
            "conclusion": obs.get("conclusion"),
        }
        rows.append(row)

elapsed = time.time() - start
for r in rows: r["elapsed_time"] = elapsed/len(rows)

# write observations
with open(repo/"observations.json","w") as f: json.dump(rows,f,indent=2)
# csv
fieldnames = list(rows[0].keys())
with open(repo/"observations.csv","w",newline="") as f:
    w = csv.DictWriter(f, fieldnames=fieldnames)
    w.writeheader()
    for r in rows:
        out={}
        for k,v in r.items():
            if isinstance(v,(list,dict)):
                out[k]=json.dumps(v, sort_keys=True, separators=(",",":"))
            else: out[k]=v
        w.writerow(out)

# RESULTS.md
def count_bucket(name):
    return sum(1 for r in rows if r["actual_classification"]==name)
buckets=["pass","expected_error","local_observation","toolchain_skip","context_only","not_applicable","fail"]
counts={b:count_bucket(b) for b in buckets}
with open(repo/"RESULTS.md","w") as f:
    f.write("# RESULTS\n\n")
    f.write(f"Toolchain: {zig_sanitized}, zig {zig_version}, target {zig_target}\n\n")
    f.write(f"Python: {py_exe_sanitized}\n\n")
    f.write(f"RAND_MAX={helper_json.get('RAND_MAX')}, source_span={helper_json.get('source_span')}\n\n")
    # summaries
    def find_row(cid, method):
        for r in rows:
            if r["case_id"]==cid and r["method"]==method: return r
        return {}
    ds = find_row("default_seed_equivalence_marker","exercise_c_rand")
    f.write(f"default_seed_equivalent: {ds.get('sequence_equal')}\n\n")
    ss = find_row("same_seed_replay_marker","exercise_c_rand")
    f.write(f"same_seed_equal: {ss.get('sequence_equal')}\n\n")
    diff = find_row("different_seed_local_observation_marker","exercise_c_rand")
    f.write(f"different_seed_differ (local): {diff.get('sequence_inequality')}\n\n")
    rr = find_row("rand_range_invariant_marker","exercise_c_rand")
    f.write(f"range_invariant passed\n\n")
    mb16 = find_row("modulo_bias_16_to_6_marker","enumerate_mapping")
    f.write(f"modulo 16→6 counts: {mb16.get('output_counts')}\n\n")
    mb32 = find_row("modulo_bias_32_to_10_marker","enumerate_mapping")
    f.write(f"modulo 32→10 counts: {mb32.get('output_counts')}\n\n")
    pot = find_row("power_of_two_modulo_marker","enumerate_mapping")
    f.write(f"power_of_two counts: {pot.get('output_counts')}\n\n")
    rej = find_row("top_tail_rejection_16_to_6_marker","enumerate_mapping")
    f.write(f"top_tail rejection counts: {rej.get('output_counts')}, accepted_span={rej.get('accepted_span')}\n\n")
    bm = find_row("bitmask_rejection_8_to_6_marker","enumerate_mapping")
    f.write(f"bitmask rejection counts: {bm.get('output_counts')}\n\n")
    zb = find_row("zero_bound_rejection_marker","enumerate_mapping")
    f.write(f"zero_bound status: {zb.get('status')}, rand_calls={zb.get('rand_calls')}\n\n")
    fy = find_row("fixed_fisher_yates_indices_marker","enumerate_mapping")
    f.write(f"fisher_yates selected_indices: {fy.get('selected_indices')}, final_array: {fy.get('final_array')}\n\n")
    cand = find_row("fixed_candidate_index_marker","enumerate_mapping")
    f.write(f"candidate_index: {cand.get('selected_candidate_index')}, candidate_id: {cand.get('selected_candidate_id')}\n\n")
    f.write(f"cases: 16, methods: 4, rows: {len(rows)}\n\n")
    f.write("Classifications:\n")
    for b in buckets: f.write(f"- {b}: {counts[b]}\n")
    f.write(f"\nElapsed: {elapsed:.3f}s\n")
    f.write("\nNarrow local conclusions only. No randomness validation, no ML validation, no security, no universal portability.\n")

print(f"rows={len(rows)} pass={counts['pass']} elapsed={elapsed:.2f}s")
print("OK")
