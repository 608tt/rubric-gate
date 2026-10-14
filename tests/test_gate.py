import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from rubric_gate.core import evaluate, footnotes
from rubric_gate.__main__ import main, render_html


class GateTests(unittest.TestCase):
    def setUp(self):
        self.spec = {"version": 1, "rules": [
            {"id": "preserve", "op": "contains_all", "values": ["Alice", "2026-10-01"], "weight": 5},
            {"id": "avoid", "op": "excludes", "values": ["guaranteed"], "weight": 1},
            {"id": "next", "op": "contains_any", "values": ["Next step", "下一步"], "hard": False},
        ]}

    def test_a_high_score_cannot_override_a_hard_gate(self):
        result = evaluate("Alice 2026-10-01 Next step guaranteed", self.spec)
        self.assertGreater(result["score"], 80)
        self.assertFalse(result["accepted"])

    def test_soft_failure_does_not_block(self):
        result = evaluate("Alice 2026-10-01", self.spec)
        self.assertTrue(result["accepted"])
        self.assertLess(result["score"], 100)

    def test_mutated_fact_is_blocked(self):
        self.assertFalse(evaluate("Alice 2026-10-02 Next step", self.spec)["accepted"])

    def test_dangling_unused_duplicate_footnotes(self):
        self.assertTrue(footnotes("Text[^1]\n\n[^1]: Source")[0])
        for text in ["Text[^1]", "Text\n[^1]: Source", "Text[^1]\n[^1]: Source\n[^1]: Another"]:
            self.assertFalse(footnotes(text)[0])

    def test_regex_length_and_hash(self):
        text = "项目 Alice"
        spec = {"version": 1, "rules": [
            {"id": "pattern", "op": "regex", "pattern": "Alice$"},
            {"id": "length", "op": "length", "unit": "chinese", "min": 2, "max": 2},
            {"id": "immutable", "op": "sha256", "value": hashlib.sha256(text.encode()).hexdigest()},
        ]}
        self.assertTrue(evaluate(text, spec)["accepted"])
        self.assertFalse(evaluate(text + "!", spec)["accepted"])

    def test_bad_specs_fail_as_configuration_errors(self):
        for mutation in [{"id": "preserve", "op": "unknown"},
                         {"id": "x", "op": "regex", "pattern": "["},
                         {"id": "x", "op": "length", "min": 10, "max": 2},
                         {"id": "x", "op": "excludes", "values": []}]:
            spec = copy.deepcopy(self.spec)
            spec["rules"].append(mutation)
            with self.assertRaises(ValueError):
                evaluate("text", spec)

    def test_boolean_weight_is_invalid(self):
        self.spec["rules"][0]["weight"] = True
        with self.assertRaises(ValueError):
            evaluate("text", self.spec)

    def test_boolean_version_and_invalid_text_are_rejected(self):
        self.spec["version"] = True
        with self.assertRaises(ValueError):
            evaluate("text", self.spec)
        self.spec["version"] = 1
        with self.assertRaises(ValueError):
            evaluate(None, self.spec)

    def test_html_escapes_rule_content(self):
        self.spec["rules"][0]["id"] = "<script>alert(1)</script>"
        page = render_html([evaluate("test", self.spec, "<img>")])
        self.assertNotIn("<script>", page)
        self.assertIn("&lt;img&gt;", page)

    def test_cli_exit_codes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            spec = root / "rules.json"
            spec.write_text(json.dumps(self.spec))
            text = root / "candidate.md"
            text.write_text("Alice 2026-10-01 Next step")
            output = root / "report.json"
            args = [str(text), "--spec", str(spec), "--output", str(output)]
            self.assertEqual(main(args), 0)
            text.write_text("Alice 2026-10-01 guaranteed")
            self.assertEqual(main(args), 1)
            spec.write_text("invalid")
            self.assertEqual(main(args), 2)

    def test_reproducible_results(self):
        self.assertEqual(evaluate("text", self.spec), evaluate("text", self.spec))


if __name__ == "__main__":
    unittest.main()
