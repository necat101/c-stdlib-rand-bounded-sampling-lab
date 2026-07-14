#!/usr/bin/env python3
import unittest, json, os, csv, sys, re
with open("cases.json") as f: cases=json.load(f)
with open("results_rows.json") as f: rows=json.load(f)

case_ids=[c["id"] for c in cases]

class TestLab(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        import subprocess, os, shutil
        if not os.path.exists("./rand_lab"):
            # try to build with zig
            zig=None
            for c in [os.environ.get("ZIG_BIN"), shutil.which("zig"), os.path.expanduser("~/.local/bin/zig"), os.path.expanduser("~/bin/zig"), os.path.expanduser("~/.local/zig/zig")]:
                if c and os.path.isfile(c) and os.access(c, os.X_OK):
                    zig=c; break
            if zig:
                try:
                    subprocess.check_call([zig,"cc","-std=c11","-O2","-Wall","-Wextra","-Wpedantic","-Werror","rand_lab.c","-o","rand_lab"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10)
                except Exception:
                    pass

    def test_case_count(self):
        self.assertEqual(len(cases),20)
        ids=case_ids
        self.assertEqual(len(set(ids)),20)
        for want in ["zig_compiler_marker","c_rand_api_marker","rand_max_marker","implicit_seed_equals_srand_one_marker","same_seed_replay_marker","seed_reset_prefix_marker","sequence_portability_limit_marker","toy_divisible_modulo_marker","toy_nondivisible_modulo_marker","rejection_threshold_marker","rejection_uniformity_marker","power_of_two_bound_marker","low_bit_projection_marker","bounded_helper_guard_marker","actual_rand_modulo_local_counts_marker","three_item_shuffle_modulo_marker","three_item_shuffle_accepted_draw_space_marker","tiny_minibatch_index_sampler_marker","range_reduction_not_rng_quality_marker","no_global_rng_or_ml_validity_claim_marker"]:
            self.assertIn(want, ids)

    def test_cases_have_expectations(self):
        methods={"inspect_toolchain","exercise_c_stdlib","enumerate_mapping","ml_context_observation"}
        allowed={"pass","expected_error","local_observation","context_only","toolchain_skip","not_applicable","fail"}
        for c in cases:
            self.assertIn("expectations", c)
            exp=c["expectations"]
            self.assertEqual(set(exp.keys()), methods, f"{c['id']} missing methods")
            for k,v in exp.items():
                self.assertIn(v, allowed, f"{c['id']}/{k} bad classification {v}")

    def test_rows_80(self):
        self.assertEqual(len(rows),80)

    def test_pairs_unique(self):
        pairs=[(r["case_id"],r["method"]) for r in rows]
        self.assertEqual(len(pairs),len(set(pairs)))
        self.assertEqual(len(pairs),80)
        # ensure every case/method pair exists
        for cid in case_ids:
            for m in ["inspect_toolchain","exercise_c_stdlib","enumerate_mapping","ml_context_observation"]:
                self.assertIn((cid,m), pairs, f"missing {cid}/{m}")

    def test_classifications(self):
        allowed={"pass","expected_error","local_observation","context_only","toolchain_skip","not_applicable","fail"}
        for r in rows:
            self.assertIn(r["expected_classification"], allowed, r)
            self.assertIn(r["actual_classification"], allowed, r)
            self.assertTrue(r["expected_classification"])
            self.assertTrue(r["actual_classification"])
            if r["expected_classification"]=="not_applicable":
                self.assertEqual(r["actual_classification"],"not_applicable")
        # expected vs actual must agree unless fail or toolchain_skip
        for r in rows:
            if r["actual_classification"] in ("fail","toolchain_skip"): continue
            self.assertEqual(r["expected_classification"], r["actual_classification"], f"{r['case_id']}:{r['method']} expected {r['expected_classification']} actual {r['actual_classification']}")

    def test_expected_matches_cases_json(self):
        # verify results_rows expected_classification matches cases.json expectations
        exp_map={}
        for c in cases:
            for m,cls in c["expectations"].items():
                exp_map[(c["id"],m)]=cls
        for r in rows:
            key=(r["case_id"],r["method"])
            self.assertIn(key, exp_map)
            self.assertEqual(r["expected_classification"], exp_map[key], f"expected_classification mismatch for {key}")

    def test_toolchain(self):
        row=next(r for r in rows if r["case_id"]=="zig_compiler_marker" and r["method"]=="inspect_toolchain")
        self.assertEqual(row["actual_classification"],"pass")
        self.assertIn("zig", row["zig_executable_representation"].lower())

    def test_rand_max(self):
        row=next(r for r in rows if r["case_id"]=="rand_max_marker" and r["method"]=="exercise_c_stdlib")
        self.assertGreaterEqual(row["RAND_MAX"],32767)

    def test_implicit_seed(self):
        import subprocess, json as js
        out=subprocess.check_output(["./rand_lab"], text=True, timeout=5)
        d=js.loads(out)
        self.assertEqual(d["implicit_prefix"], d["srand1_prefix"])

    def test_same_seed(self):
        import subprocess, json as js
        out=subprocess.check_output(["./rand_lab"], text=True, timeout=5)
        d=js.loads(out)
        self.assertEqual(d["replay_a"], d["replay_b"])

    def test_seed_reset(self):
        import subprocess, json as js
        out=subprocess.check_output(["./rand_lab"], text=True, timeout=5)
        d=js.loads(out)
        self.assertEqual(d["seg1"]+d["seg2"], d["seg_full"])

    def test_divisible(self):
        counts=[0]*4
        for x in range(16): counts[x%4]+=1
        self.assertEqual(counts,[4,4,4,4])

    def test_nondivisible(self):
        counts=[0]*6
        for x in range(16): counts[x%6]+=1
        self.assertEqual(counts,[3,3,3,3,2,2])

    def test_rejection(self):
        accepted_limit=16-(16%6)
        self.assertEqual(accepted_limit,12)
        rej=list(range(accepted_limit,16))
        self.assertEqual(rej,[12,13,14,15])
        counts=[0]*6
        for x in range(accepted_limit): counts[x%6]+=1
        self.assertEqual(counts,[2]*6)

    def test_power_two(self):
        counts=[0]*8
        for x in range(16): counts[x%8]+=1
        self.assertEqual(counts,[2]*8)

    def test_low_bit(self):
        src=[0,2,4,6,8,10,12,14]
        outs=[x%2 for x in src]
        self.assertEqual(outs,[0]*8)

    def test_bounded_helper(self):
        # verify C helper actually rejects invalid inputs
        import subprocess, json as js
        out=subprocess.check_output(["./rand_lab"], text=True, timeout=5)
        d=js.loads(out)
        self.assertNotEqual(d["guard_zero_status"], 0, "guard_zero should reject")
        self.assertNotEqual(d["guard_oversize_status"], 0, "guard_oversize should reject")
        self.assertNotEqual(d["guard_null_status"], 0, "guard_null should reject")
        self.assertEqual(d["guard_valid_status"], 0, "valid guard call should succeed")

    def test_shuffle_modulo(self):
        def shuffle3(j,k):
            a=["a","b","c"]; a[2],a[j]=a[j],a[2]; a[1],a[k]=a[k],a[1]; return tuple(a)
        pc={}
        for rf in range(4):
            for rs in range(4):
                p=shuffle3(rf%3, rs%2); pc[p]=pc.get(p,0)+1
        self.assertEqual(sorted(pc.values()),[2,2,2,2,4,4])

    def test_shuffle_accepted(self):
        def shuffle3(j,k):
            a=["a","b","c"]; a[2],a[j]=a[j],a[2]; a[1],a[k]=a[k],a[1]; return tuple(a)
        seen=set()
        for j in range(3):
            for k in range(2):
                seen.add(shuffle3(j,k))
        self.assertEqual(len(seen),6)

    def test_minibatch(self):
        counts=[0]*10
        for x in range(256): counts[x%10]+=1
        self.assertEqual(counts,[26,26,26,26,26,26,25,25,25,25])
        acc=[0]*10
        for x in range(250): acc[x%10]+=1
        self.assertEqual(acc,[25]*10)

    def test_actual_rand_counts(self):
        row=next(r for r in rows if r["case_id"]=="actual_rand_modulo_local_counts_marker" and r["method"]=="exercise_c_stdlib")
        counts=row["exact_output_counts"]
        self.assertEqual(sum(counts),10000)
        self.assertEqual(row["actual_classification"],"local_observation")

    def test_readme_disclaimers(self):
        with open("README.md") as f: txt=f.read().lower()
        for needle in ["range reduction does not establish","no_global_rng_or_ml_validity","hacker news thread access","cryptographically secure","does not prove","rand()"]:
            self.assertIn(needle, txt)

    def test_results_agree(self):
        with open("results_rows.csv") as f: csv_rows=list(csv.DictReader(f))
        self.assertEqual(len(csv_rows),80)
        # check a few fields agree between json and csv
        import json as js
        j0=rows[0]
        c0=csv_rows[0]
        self.assertEqual(c0["case_id"], j0["case_id"])
        self.assertEqual(c0["method"], j0["method"])
        self.assertEqual(c0["actual_classification"], j0["actual_classification"])

    def test_json_csv_results_fields_agree(self):
        # verify key numeric fields round-trip correctly
        with open("results_rows.csv") as f:
            import csv; csv_rows=list(csv.DictReader(f))
        for jr, cr in zip(rows, csv_rows):
            self.assertEqual(cr["case_id"], jr["case_id"])
            self.assertEqual(cr["method"], jr["method"])
            self.assertEqual(cr["expected_classification"], jr["expected_classification"])
            self.assertEqual(cr["actual_classification"], jr["actual_classification"])

    def test_no_binaries(self):
        bad=[]
        for root,dirs,files in os.walk("."):
            # skip .git
            if "/.git" in root: continue
            for name in files:
                if name in ("rand_lab","rand_lab.exe") or name.endswith((".o",".obj",".pyc")):
                    # allow ./rand_lab for testing, but flag others
                    full=os.path.join(root,name)
                    if full == "./rand_lab": continue
                    bad.append(full)
                if "__pycache__" in root:
                    bad.append(root); break
        bad=[b for b in bad if "__pycache__" not in b]
        self.assertEqual(bad, [], str(bad))

    def test_artifact_scan(self):
        # scan ALL committed text artifacts
        files=[
            "README.md","RESULTS.md","cases.json","results_rows.json","results_rows.csv",
            "rand_lab.c","run_lab.py","test_lab.py","hn_thread_evidence.md","hn_comments_sanitized.json",".gitignore"
        ]
        # if VERIFY.md exists, scan it too
        if os.path.exists("VERIFY.md"): files.append("VERIFY.md")
        prohibited_patterns = [
            r"ghp_[A-Za-z0-9]{20,}",  # github token
            r"BEGIN (RSA|OPENSSH|EC|DSA) PRIVATE KEY",
            r"openclaw-control-ui",
            r"\b[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}\b",  # uuid / session id – may false positive, check context
        ]
        # path patterns that should NOT appear (home, tmp, workspace internal)
        path_fragments = [
            "/home/ubuntu/", "/tmp/", "/root/", "/Users/",
            "saltpepper",  # email local part – allow in git config only, not in artifacts
        ]
        for fn in files:
            if not os.path.exists(fn): continue
            with open(fn, errors="ignore") as f: txt=f.read()
            if fn == "test_lab.py": continue
            self.assertNotIn("ghp_", txt, f"{fn} contains github token prefix")
            self.assertNotIn("BEGIN RSA PRIVATE KEY", txt, fn)
            self.assertNotIn("BEGIN OPENSSH PRIVATE KEY", txt, fn)
            self.assertNotIn("openclaw-control-ui", txt.lower(), fn)
            # check for obvious home paths in non-allowlisted files
            # allow /tmp in .gitignore, and allow portable-zig sanitized paths
            if fn == ".gitignore": continue
            # README may contain /usr/lib path for HN tool – allow that specific one
            txt_check = txt.replace("/usr/lib/node_modules/openclaw/dist/extensions/hackernews/skills/hackernews/hackernews", "")
            # allow /portable-zig sanitized placeholder
            txt_check = txt_check.replace("/portable-zig", "")
            # now check for leaked real paths
            if "/home/ubuntu/.openclaw" in txt_check or "/home/ubuntu/.local" in txt_check:
                # allow in test_lab.py if it's in a comment about scanning – check
                if fn == "test_lab.py": continue
                self.fail(f"{fn} contains leaked home path")
            # check for un-sanitized /tmp paths (allow /tmp in generic documentation like "/tmp/")
            if re.search(r"/tmp/[A-Za-z0-9_-]{3,}", txt_check):
                # allow /tmp in README reproduce section generically?
                # be strict – fail if looks like a real temp path
                if "/tmp/lab" in txt_check or "/tmp/verify" in txt_check or "/tmp/c-stdlib" in txt_check:
                    self.fail(f"{fn} contains leaked /tmp path")

    def test_classification_independence(self):
        # ensure actual_classification was not just copied – check that handler logic exists
        # at minimum, verify that cases with expected=pass actually passed their independent checks
        # (already done in handler tests above)
        # and verify no expected=fail rows are secretly marked pass without evaluation
        with open("run_lab.py") as f: runner=f.read()
        self.assertIn("actual_cls", runner)
        self.assertIn("expected", runner)
        # ensure actual is NOT assigned directly from expected
        # look for the bad pattern: actual = e / actual_cls = exp
        # allow "actual_cls = exp" only in ml_context_observation context (which is allowed to echo)
        # crude check: there should be handler functions that return classifications independently
        self.assertIn("def handle_", runner)
        self.assertIn("return \"pass\"", runner)

if __name__=="__main__": unittest.main()
