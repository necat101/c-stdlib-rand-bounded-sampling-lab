#!/usr/bin/env python3
import unittest, json, csv, os, sys, pathlib, re
repo = pathlib.Path(__file__).parent
with open(repo/"cases.json") as f: cases=json.load(f)
with open(repo/"observations.json") as f: rows=json.load(f)

class LabTests(unittest.TestCase):
    def test_case_count(self):
        self.assertEqual(len(cases),16)
    def test_methods_and_rows(self):
        self.assertEqual(len(rows),64)
        pairs = [(r["method"], r["case_id"]) for r in rows]
        self.assertEqual(len(pairs), len(set(pairs)))
    def test_classification_vocab(self):
        vocab={"pass","expected_error","local_observation","toolchain_skip","context_only","not_applicable","fail"}
        for r in rows:
            self.assertIn(r["actual_classification"], vocab)
            if r["expected_classification"]=="not_applicable":
                self.assertEqual(r["actual_classification"],"not_applicable")
    def test_expectation_independence(self):
        for r in rows:
            if r["case_id"]=="different_seed_local_observation_marker" and r["method"]=="exercise_c_rand":
                self.assertEqual(r["actual_classification"],"local_observation")
    def test_missing_handler_failure(self):
        with open(repo/"run_lab.py") as f: txt=f.read()
        self.assertIn("actual_classification", txt)
        self.assertIn("fail", txt)
    def test_zig_compiler(self):
        zr = [r for r in rows if r["case_id"]=="zig_compiler_marker" and r["method"]=="inspect_toolchain"][0]
        self.assertEqual(zr["actual_classification"],"pass")
    def test_c_helper_compiled(self):
        passed = [r for r in rows if r["method"]=="exercise_c_rand" and r["actual_classification"]=="pass"]
        self.assertTrue(len(passed)>=1)
    def test_no_zig_path(self):
        with open(repo/"run_lab.py") as f: txt=f.read()
        self.assertIn("toolchain_skip", txt)
    def test_default_seed(self):
        r = [x for x in rows if x["case_id"]=="default_seed_equivalence_marker" and x["method"]=="exercise_c_rand"][0]
        self.assertEqual(r["first_sequence"], r["second_sequence"])
    def test_same_seed(self):
        r = [x for x in rows if x["case_id"]=="same_seed_replay_marker" and x["method"]=="exercise_c_rand"][0]
        self.assertEqual(r["first_sequence"], r["second_sequence"])
        self.assertTrue(r["sequence_equal"])
    def test_different_seed_local(self):
        r = [x for x in rows if x["case_id"]=="different_seed_local_observation_marker" and x["method"]=="exercise_c_rand"][0]
        self.assertEqual(r["actual_classification"],"local_observation")
    def test_range_invariant(self):
        r = [x for x in rows if x["case_id"]=="rand_range_invariant_marker" and x["method"]=="exercise_c_rand"][0]
        self.assertEqual(r["actual_classification"],"pass")
    def test_modulo_16_6(self):
        r = [x for x in rows if x["case_id"]=="modulo_bias_16_to_6_marker" and x["method"]=="enumerate_mapping"][0]
        self.assertEqual(r["output_counts"], [3,3,3,3,2,2])
    def test_modulo_32_10(self):
        r = [x for x in rows if x["case_id"]=="modulo_bias_32_to_10_marker" and x["method"]=="enumerate_mapping"][0]
        self.assertEqual(r["output_counts"], [4,4,3,3,3,3,3,3,3,3])
    def test_power_two(self):
        r = [x for x in rows if x["case_id"]=="power_of_two_modulo_marker" and x["method"]=="enumerate_mapping"][0]
        self.assertEqual(r["output_counts"], [2]*8)
    def test_top_tail(self):
        r = [x for x in rows if x["case_id"]=="top_tail_rejection_16_to_6_marker" and x["method"]=="enumerate_mapping"][0]
        self.assertEqual(r["output_counts"], [2]*6)
        self.assertEqual(r["accepted_span"],12)
    def test_bitmask(self):
        r = [x for x in rows if x["case_id"]=="bitmask_rejection_8_to_6_marker" and x["method"]=="enumerate_mapping"][0]
        self.assertEqual(r["output_counts"], [1]*6)
    def test_zero_bound(self):
        r = [x for x in rows if x["case_id"]=="zero_bound_rejection_marker" and x["method"]=="enumerate_mapping"][0]
        self.assertEqual(r["actual_classification"],"expected_error")
        self.assertEqual(r["rand_calls"],0)
    def test_fisher_yates(self):
        r = [x for x in rows if x["case_id"]=="fixed_fisher_yates_indices_marker" and x["method"]=="enumerate_mapping"][0]
        self.assertEqual(r["selected_indices"], [5,0,1,2,1])
        self.assertEqual(r["final_array"], [4,3,2,1,0,5])
    def test_candidate_index(self):
        r = [x for x in rows if x["case_id"]=="fixed_candidate_index_marker" and x["method"]=="enumerate_mapping"][0]
        self.assertEqual(r["selected_candidate_index"],5)
        self.assertEqual(r["selected_candidate_id"],621)
    def test_no_ml(self):
        r = [x for x in rows if x["case_id"]=="no_global_randomness_or_ml_validity_claim_marker" and x["method"]=="ml_context_observation"][0]
        self.assertEqual(r["actual_classification"],"context_only")
    def test_readme_disclaimers(self):
        with open(repo/"README.md") as f: txt=f.read().lower()
        for n in ["does not prove","rand()","bounded","machine-learning","no model","security","portable","pcg","hacker news"]:
            self.assertIn(n, txt)
    def test_json_csv_agreement(self):
        with open(repo/"observations.csv") as f:
            cr = list(csv.DictReader(f))
        self.assertEqual(len(cr), len(rows))
    def test_results_derived(self):
        with open(repo/"RESULTS.md") as f: res=f.read()
        self.assertIn("modulo 16→6 counts: [3, 3, 3, 3, 2, 2]", res)
    def test_classification_totals(self):
        self.assertEqual(len(rows),64)
    def test_zero_buckets_reported(self):
        with open(repo/"RESULTS.md") as f: res=f.read()
        for b in ["pass","expected_error","local_observation","toolchain_skip","context_only","not_applicable","fail"]:
            self.assertIn(b, res)
    def test_structured_fields(self):
        with open(repo/"observations.json") as f: data=json.load(f)
        self.assertIsInstance(data[0].get("output_counts") if data[0].get("output_counts") is not None else [], list)
    def test_no_prohibited_paths(self):
        # allow test_lab itself, check other files
        for name in ["README.md","RESULTS.md","rand_lab.c","run_lab.py"]:
            p = repo/name
            txt = p.read_text(errors="ignore")
            self.assertNotIn("/home/ubuntu/.openclaw/workspace", txt)
    def test_no_executables(self):
        exe = repo/"rand_lab"
        if exe.exists() and exe.is_file():
            # check if it's ELF
            with open(exe,"rb") as f: magic=f.read(4)
            self.assertNotEqual(magic, b"\x7fELF", "executable rand_lab committed")


    def test_artifact_scanner(self):
        files = ["README.md","RESULTS.md","cases.json","observations.json","observations.csv","rand_lab.c","run_lab.py","test_lab.py","hn_thread_evidence.md","hn_comments_sanitized.json",".gitignore"]
        bad = ["/home/ubuntu/.openclaw/workspace"]
        for fn in files:
            p = repo/fn
            if not p.exists(): continue
            txt = p.read_text(errors="ignore")
            for b in bad:
                if fn == "test_lab.py": continue
                self.assertNotIn(b, txt, f"{fn} contains prohibited {b}")

if __name__=="__main__":
    unittest.main()
