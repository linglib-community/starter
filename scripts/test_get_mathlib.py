"""Tests for get_mathlib.py that need neither Lean nor a network connection.

    python3 -m unittest discover -s scripts -p 'test_*.py'
"""

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import get_mathlib as gm  # noqa: E402


class HeaderImports(unittest.TestCase):
    def check(self, text, expected):
        self.assertEqual(gm.header_imports(text), expected)

    def test_plain_imports(self):
        self.check("import A.B\nimport C\n\ndef x := 1\n", ["A.B", "C"])

    def test_module_system_forms(self):
        self.check(
            "module\n\npublic import A\nmeta import B\npublic meta import C\nimport all D\n"
            "import E\n\n@[expose] public section\n",
            ["A", "B", "C", "D", "E"])

    def test_prelude(self):
        self.check("prelude\nimport Init.Core\n", ["Init.Core"])
        self.check("module\nprelude\npublic import Init.Core\n", ["Init.Core"])

    def test_copyright_block_before_imports(self):
        self.check("/-\nCopyright (c) someone.\nimport Not.This\n-/\nimport A\n", ["A"])

    def test_nested_block_comment(self):
        self.check("/- outer /- inner import X -/ still a comment import Y -/\nimport A\n", ["A"])

    def test_comments_between_imports(self):
        self.check(
            "import A -- why\n-- import Skipped\n/-- a doc comment -/\nimport B\n"
            "/-! module doc -/\nimport C\n",
            ["A", "B", "C"])

    def test_comment_touching_the_name(self):
        self.check("import A--note\nimport B/- note -/\nimport C\n", ["A", "B", "C"])

    def test_stops_at_first_declaration(self):
        for rest in ("namespace N", "open Lean", "set_option autoImplicit false", "public section",
                     "@[expose] public section", "def import := 1", "theorem t : True := trivial"):
            self.check("import A\n\n%s\nimport B\n" % rest, ["A"])

    def test_module_doc_does_not_end_the_header_but_code_does(self):
        self.check("import A\n\n/-! # Title\nimport Fake -/\n\nnamespace N\nimport B\n", ["A"])

    def test_two_imports_on_one_line(self):
        self.check("import A import B\n", ["A", "B"])

    def test_windows_line_endings(self):
        self.check("module\r\n\r\npublic import A\r\nimport B\r\n\r\ndef x := 1\r\n", ["A", "B"])

    def test_no_imports(self):
        self.check("", [])
        self.check("-- only a comment\n", [])
        self.check("def x := 1\n", [])
        self.check("/- never closed\nimport A\n", [])


class Batches(unittest.TestCase):
    def test_every_module_once_and_within_the_limit(self):
        modules = ["Mathlib.Some.Module%d" % i for i in range(1000)]
        parts = list(gm.batches(modules, limit=500))
        self.assertEqual([m for part in parts for m in part], modules)
        self.assertTrue(all(sum(len(m) + 1 for m in part) <= 500 for part in parts))
        self.assertGreater(len(parts), 1)

    def test_empty(self):
        self.assertEqual(list(gm.batches([])), [])


def write(path: Path, text: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


class Project(unittest.TestCase):
    """A small made-up project: MyProject -> Linglib -> Mathlib and Batteries."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = root = Path(self.tmp.name).resolve()
        pk = root / ".lake" / "packages"
        write(root / "lakefile.toml", 'name = "my_project"\n')
        write(root / "lean-toolchain", "leanprover/lean4:v4.34.1\n")
        write(root / "lake-manifest.json", json.dumps({
            "packagesDir": ".lake/packages",
            "packages": [{"name": "mathlib", "rev": "abc"}, {"name": "linglib", "rev": "def"}]}))
        write(root / "MyProject.lean", "import MyProject.Example\n")
        write(root / "MyProject" / "Example.lean", "import Linglib.Core\nimport Init.Data\n")
        write(root / "MyProject" / "Other.lean", "import Linglib.Extra\n")
        write(pk / "linglib" / "Linglib" / "Core.lean",
              "module\n\npublic import Mathlib.A\npublic import Batteries.Direct\n")
        write(pk / "linglib" / "Linglib" / "Extra.lean", "import Linglib.Core\nimport Mathlib.C\n")
        write(pk / "mathlib" / "lake-manifest.json", json.dumps({
            "packages": [{"name": "batteries"}, {"name": "aesop"}]}))
        write(pk / "mathlib" / "Mathlib" / "A.lean", "import Mathlib.B\nimport Aesop\n")
        write(pk / "mathlib" / "Mathlib" / "B.lean", "import Batteries.Deep\n")
        write(pk / "mathlib" / "Mathlib" / "C.lean", "import Mathlib.B\n")
        write(pk / "mathlib" / "Mathlib" / "Unused.lean", "")
        write(pk / "batteries" / "Batteries" / "Direct.lean", "")
        write(pk / "batteries" / "Batteries" / "Deep.lean", "")
        write(pk / "aesop" / "Aesop.lean", "")
        self.ws = gm.Workspace(root)

    def tearDown(self):
        self.tmp.cleanup()

    def olean(self, package: str, module: str) -> Path:
        return self.ws.olean(self.root / ".lake" / "packages" / package, module)

    def test_needed_and_asked_for(self):
        needed, ask = gm.needed_files(self.ws, ["MyProject.Example"])
        self.assertEqual(set(needed),
                         {"Mathlib.A", "Mathlib.B", "Aesop", "Batteries.Direct", "Batteries.Deep"})
        # Only what is imported directly from outside Mathlib and its packages is asked for.
        self.assertEqual(ask, {"Mathlib.A", "Batteries.Direct"})

    def test_a_second_importer_from_outside_is_asked_for_too(self):
        _, ask = gm.needed_files(self.ws, ["MyProject.Example", "MyProject.Other"])
        self.assertEqual(ask, {"Mathlib.A", "Batteries.Direct", "Mathlib.C"})

    def test_default_targets_are_the_project_files(self):
        self.assertEqual(gm.project_modules(self.root),
                         ["MyProject", "MyProject.Example", "MyProject.Other"])

    def test_target_given_as_a_path(self):
        path = str(self.root / "MyProject" / "Example.lean")
        self.assertEqual(gm.as_module(self.root, path), "MyProject.Example")
        with self.assertRaises(gm.Problem):
            gm.as_module(self.root, str(self.root / "MyProject" / "Missing.lean"))

    def test_unknown_target(self):
        with self.assertRaises(gm.Problem):
            gm.needed_files(self.ws, ["MyProject.NoSuchFile"])

    def test_check_mode(self):
        argv = ["--dir", str(self.root), "--check", "MyProject.Example"]
        self.assertEqual(gm.main(argv), 1)
        for package, module in (("mathlib", "Mathlib.A"), ("mathlib", "Mathlib.B"),
                                ("aesop", "Aesop"), ("batteries", "Batteries.Direct")):
            write(self.olean(package, module))
        self.assertEqual(gm.main(argv), 1)          # Batteries.Deep is still missing
        write(self.olean("batteries", "Batteries.Deep"))
        self.assertEqual(gm.main(argv), 0)
        # A file another module needs does not affect this one.
        self.assertEqual(gm.main(["--dir", str(self.root), "--check"]), 1)
        write(self.olean("mathlib", "Mathlib.C"))
        self.assertEqual(gm.main(["--dir", str(self.root), "--check"]), 0)

    def test_check_fails_after_a_version_change(self):
        for package, module in (("mathlib", "Mathlib.A"), ("mathlib", "Mathlib.B"),
                                ("aesop", "Aesop"), ("batteries", "Batteries.Direct"),
                                ("batteries", "Batteries.Deep")):
            write(self.olean(package, module))
        argv = ["--dir", str(self.root), "--check", "MyProject.Example"]
        write(self.ws.stamp, self.ws.mathlib_version() + "\n")
        self.assertEqual(gm.main(argv), 0)
        write(self.ws.stamp, "an older revision\n")
        self.assertEqual(gm.main(argv), 1)

    def test_no_packages_yet(self):
        with tempfile.TemporaryDirectory() as empty:
            write(Path(empty) / "lakefile.toml", "")
            self.assertEqual(gm.main(["--dir", empty, "--check"]), 2)


if __name__ == "__main__":
    unittest.main()
