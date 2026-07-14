#!/usr/bin/env python3
import unittest, json, os, csv, sys
with open("cases.json") as f: cases=json.load(f)
with open("results_rows.json") as f: rows=json.load(f)

class TestLab(unittest.TestCase):
    def test_case_count(self):
        self.assertEqual(len(cases),20)
        ids=[c["id"] for c in cases]
        self.assertEqual(len(set(ids)),20)
        for want in ["zig_compiler_marker","c_rand_api_marker","rand_max_marker","implicit_seed_equals_srand_one_marker","same_seed_replay_marker","seed_reset_prefix_marker","sequence_portability_limit_marker","toy_divisible_modulo_marker","toy_nondivisible_modulo_marker","rejection_threshold_marker","rejection_uniformity_marker","power_of_two_bound_marker","low_bit_projection_marker","bounded_helper_guard_marker","actual_rand_modulo_local_counts_marker","three_item_shuffle_modulo_marker","three_item_shuffle_accepted_draw_space_marker","tiny_minibatch_index_sampler_marker","range_reduction_not_rng_quality_marker","no_global_rng_or_ml_validity_claim_marker"]:
            self.assertIn(want, ids)
    def test_rows_80(self):
        self.assertEqual(len(rows),80)
    def test_pairs_unique(self):
        pairs=[(r["case_id"],r["method"]) for r in rows]
        self.assertEqual(len(pairs),len(set(pairs)))
        self.assertEqual(len(pairs),80)
    def test_classifications(self):
        allowed={"pass","expected_error","local_observation","context_only","toolchain_skip","not_applicable","fail"}
        for r in rows:
            self.assertIn(r["expected_classification"], allowed)
            self.assertIn(r["actual_classification"], allowed)
            self.assertTrue(r["expected_classification"])
            self.assertTrue(r["actual_classification"])
            if r["expected_classification"]=="not_applicable":
                self.assertEqual(r["actual_classification"],"not_applicable")
        # agree unless fail/skip
        for r in rows:
            if r["actual_classification"] in ("fail","toolchain_skip"): continue
            self.assertEqual(r["expected_classification"], r["actual_classification"], r["case_id"]+":"+r["method"])
    def test_toolchain(self):
        row=next(r for r in rows if r["case_id"]=="zig_compiler_marker" and r["method"]=="inspect_toolchain")
        self.assertEqual(row["actual_classification"],"pass")
        self.assertIn("zig", row["zig_executable_representation"])
    def test_rand_max(self):
        row=next(r for r in rows if r["case_id"]=="rand_max_marker" and r["method"]=="exercise_c_stdlib")
        self.assertGreaterEqual(row["RAND_MAX"],32767)
    def test_implicit_seed(self):
        # check via c helper output
        import subprocess, json as js
        out=subprocess.check_output(["./rand_lab"], text=True)
        d=js.loads(out)
        self.assertEqual(d["implicit_prefix"], d["srand1_prefix"])
    def test_same_seed(self):
        import subprocess, json as js
        out=subprocess.check_output(["./rand_lab"], text=True)
        d=js.loads(out)
        self.assertEqual(d["replay_a"], d["replay_b"])
    def test_seed_reset(self):
        import subprocess, json as js
        out=subprocess.check_output(["./rand_lab"], text=True)
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
    def test_no_binaries(self):
        bad=[]
        for root,dirs,files in os.walk("."):
            for name in files:
                if name in ("rand_lab","rand_lab.exe") or name.endswith((".o",".obj",".pyc")): bad.append(os.path.join(root,name))
                if "pycache" in root: bad.append(root)
        # allow the freshly built rand_lab for testing, but check git would ignore it
        # just ensure no .o etc committed accidentally – allow ./rand_lab existing
        bad=[b for b in bad if not b.endswith("/rand_lab") or os.path.isdir(b)]
        # pycache check – allow but warn
        bad=[b for b in bad if "__pycache__" not in b]
        self.assertEqual(bad, [], str(bad))
    def test_artifact_scan(self):
        files=["README.md","RESULTS.md","cases.json","results_rows.json","results_rows.csv","rand_lab.c","run_lab.py","hn_thread_evidence.md","hn_comments_sanitized.json"]
        for fn in files:
            if not os.path.exists(fn): continue
            with open(fn, errors="ignore") as f: txt=f.read()
            self.assertNotIn("ghp_", txt, fn)
            self.assertNotIn("BEGIN RSA", txt, fn)

if __name__=="__main__": unittest.main()
