#!/usr/bin/env python3
"""Download the prebuilt Mathlib files this project needs, and no others.

All of Mathlib's prebuilt files take about 7 GB; a project uses a small part of them. This
script follows the `import` lines from the project's own Lean files (or from the modules or
files named as arguments) through linglib and the other packages in `.lake/packages`, finds the
Mathlib files that are reached, and asks Mathlib's own download tool for exactly those:

    lake exe cache get <modules>

Run it from the project folder before `lake build` whenever an `import` line has changed (in
the linglib starter, `scripts/build.sh` does both). Lean compiles any Mathlib file that is
needed but was not downloaded, and that takes hours.

    python3 get_mathlib.py                     # all that the project's own files import
    python3 get_mathlib.py MyProject.Example   # one module, or a path to a .lean file
    python3 get_mathlib.py --check             # download nothing; exit 1 if any is missing

Exit status: 0 when every needed file is present, 1 when some are missing or a download failed,
2 when the project is not set up far enough to tell (for example, no packages yet).

Python 3.8 or later, standard library only. Works on macOS, Linux and Windows.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Tuple

# ---------------------------------------------------------------------------------------------
# Reading the imports of a Lean file
# ---------------------------------------------------------------------------------------------

_SKIP = re.compile(r"\s+|--[^\n]*")            # whitespace and line comments
_TOKEN = re.compile(r"(?:(?!--|/-)\S)+")       # a word, ending where a comment starts
_COMMENT_EDGE = re.compile(r"/-|-/")
_MODIFIERS = {"public", "private", "meta"}


def _skip_block_comment(text: str, pos: int) -> int:
    """The position just after the block comment that opens at `pos`. Comments nest."""
    depth, pos = 1, pos + 2
    while depth:
        edge = _COMMENT_EDGE.search(text, pos)
        if edge is None:
            return len(text)
        depth += 1 if edge.group(0) == "/-" else -1
        pos = edge.end()
    return pos


def header_imports(text: str) -> List[str]:
    """The modules a Lean file imports.

    A Lean file opens with a header: optionally `module`, optionally `prelude`, then its imports,
    each of the form `[public] [meta] import [all] Some.Module`. Comments may come before and
    between them. The header ends at the first word that is not part of it.
    """
    imports: List[str] = []
    pos, expect_name, seen_all = 0, False, False
    while pos < len(text):
        skipped = _SKIP.match(text, pos)
        if skipped:
            pos = skipped.end()
            continue
        if text.startswith("/-", pos):
            pos = _skip_block_comment(text, pos)
            continue
        word = _TOKEN.match(text, pos)
        if word is None:
            break
        token, pos = word.group(0), word.end()
        if expect_name:
            if token == "all" and not seen_all:
                seen_all = True
                continue
            imports.append(token)
            expect_name = False
        elif token == "import":
            expect_name, seen_all = True, False
        elif token in _MODIFIERS:
            continue
        elif token in ("module", "prelude") and not imports:
            continue
        else:
            break
    return imports


# ---------------------------------------------------------------------------------------------
# The project and its packages
# ---------------------------------------------------------------------------------------------

class Problem(Exception):
    """Something the user has to fix before this script can do its job."""


def find_project_root(start: Path) -> Path:
    """The nearest folder at or above `start` that holds a lakefile."""
    for folder in [start, *start.parents]:
        if (folder / "lakefile.toml").is_file() or (folder / "lakefile.lean").is_file():
            return folder
    raise Problem(f"No lakefile.toml or lakefile.lean found in {start} or the folders above it.")


def _read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


class Workspace:
    """Where each module's source file is, and which packages Mathlib's download tool serves."""

    def __init__(self, root: Path):
        self.root = root
        self.manifest = _read_json(root / "lake-manifest.json")
        self.packages_dir = root / self.manifest.get("packagesDir", ".lake/packages")
        self.mathlib = self.packages_dir / "mathlib"
        if not self.mathlib.is_dir():
            raise Problem(
                "Mathlib has not been downloaded into this project yet "
                f"({self.mathlib} does not exist). Run the project's setup first.")
        packages = sorted(p for p in self.packages_dir.iterdir() if p.is_dir())
        self.source_roots: List[Path] = [root, *packages]
        # Mathlib's download tool serves Mathlib and the packages Mathlib itself depends on.
        names = {"mathlib"}
        for package in _read_json(self.mathlib / "lake-manifest.json").get("packages", []):
            names.add(str(package.get("name", "")).strip("«»"))
        self.served: Set[Path] = {self.packages_dir / name for name in names}
        self._candidates: Dict[str, List[Path]] = {}

    def locate(self, module: str) -> Optional[Tuple[Path, Path]]:
        """The source root and file of a module, or None for a module that comes with Lean."""
        parts = module.split(".")
        top = parts[0]
        if top not in self._candidates:
            self._candidates[top] = [
                r for r in self.source_roots
                if (r / top).is_dir() or (r / (top + ".lean")).is_file()]
        for source_root in self._candidates[top]:
            path = source_root.joinpath(*parts[:-1], parts[-1] + ".lean")
            if path.is_file():
                return source_root, path
        return None

    def olean(self, source_root: Path, module: str) -> Path:
        parts = module.split(".")
        built = source_root.joinpath(".lake", "build", "lib", "lean")
        return built.joinpath(*parts[:-1], parts[-1] + ".olean")

    def mathlib_version(self) -> str:
        """What the downloaded files must match: Mathlib's revision and the Lean version."""
        rev = next((p.get("rev", "") for p in self.manifest.get("packages", [])
                    if str(p.get("name", "")).strip("«»") == "mathlib"), "")
        try:
            toolchain = (self.root / "lean-toolchain").read_text(encoding="utf-8").strip()
        except OSError:
            toolchain = ""
        return f"{rev} {toolchain}".strip()

    @property
    def stamp(self) -> Path:
        return self.mathlib / ".lake" / "build" / "get_mathlib.version"


def project_modules(root: Path) -> List[str]:
    """Every Lean file of the project itself, as module names."""
    modules = []
    for folder, subfolders, files in os.walk(root):
        subfolders[:] = sorted(d for d in subfolders if not d.startswith("."))
        for name in sorted(files):
            if name.endswith(".lean") and name != "lakefile.lean":
                rel = Path(folder, name).relative_to(root).with_suffix("")
                modules.append(".".join(rel.parts))
    return modules


def as_module(root: Path, target: str) -> str:
    """A target given as a module name or as a path to a .lean file, as a module name."""
    if not (target.endswith(".lean") or "/" in target or "\\" in target):
        return target
    path = Path(target)
    path = path if path.is_absolute() else Path.cwd() / path
    try:
        rel = path.resolve().relative_to(root.resolve())
    except ValueError:
        raise Problem(f"{target} is not inside the project folder {root}.")
    if not path.is_file():
        raise Problem(f"{target} does not exist.")
    return ".".join(rel.with_suffix("").parts)


def needed_files(ws: Workspace, targets: Iterable[str]) -> Tuple[Dict[str, Path], Set[str]]:
    """Follow imports from the targets.

    Returns the modules reached that Mathlib's download tool serves (with their source roots),
    and the ones among them to ask the tool for: those imported directly from outside, since
    the tool fetches whatever they import in turn.
    """
    needed: Dict[str, Path] = {}
    ask: Set[str] = set()
    seen: Set[str] = set()
    stack = []
    for target in targets:
        if ws.locate(target) is None:
            raise Problem(f"Cannot find the module {target} in this project or its packages.")
        stack.append((target, True))
    while stack:
        module, from_outside = stack.pop()
        found = ws.locate(module)
        if found is None:
            continue
        source_root, path = found
        served = source_root in ws.served
        if served:
            needed[module] = source_root
            if from_outside:
                ask.add(module)
        if module in seen:
            continue
        seen.add(module)
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for imported in header_imports(text):
            if imported not in seen or not served:
                stack.append((imported, not served))
    return needed, ask


# ---------------------------------------------------------------------------------------------
# Downloading
# ---------------------------------------------------------------------------------------------

def find_lake() -> str:
    lake = shutil.which("lake")
    if lake:
        return lake
    for name in ("lake", "lake.exe"):
        candidate = Path.home() / ".elan" / "bin" / name
        if candidate.is_file():
            return str(candidate)
    raise Problem("Cannot find `lake`. Is Lean installed? (It lives in ~/.elan/bin.)")


def batches(modules: List[str], limit: int = 6000) -> Iterable[List[str]]:
    """Split a long list so that no command line exceeds what Windows accepts."""
    batch: List[str] = []
    size = 0
    for module in modules:
        if batch and size + len(module) + 1 > limit:
            yield batch
            batch, size = [], 0
        batch.append(module)
        size += len(module) + 1
    if batch:
        yield batch


def say(text: str) -> None:
    try:
        print(text, flush=True)
    except UnicodeEncodeError:
        print(text.encode("ascii", "replace").decode("ascii"), flush=True)


def download(ws: Workspace, ask: Set[str], verbose: bool) -> bool:
    """Run Mathlib's download tool on the given modules. False if it reports a failure."""
    lake = find_lake()
    for batch in batches(sorted(ask)):
        command = [lake, "exe", "cache", "get", *batch]
        if verbose:
            say("running: lake exe cache get <%d modules>" % len(batch))
        result = subprocess.run(
            command, cwd=str(ws.root), stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            universal_newlines=True, encoding="utf-8", errors="replace")
        if verbose or result.returncode != 0:
            say(result.stdout.rstrip()[-6000:])
        if result.returncode != 0:
            say("Mathlib's download tool failed (exit code %d). This step needs internet access "
                "to github.com and cache.mathlib.org." % result.returncode)
            return False
    return True


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Download the prebuilt Mathlib files this project needs, and no others.")
    parser.add_argument("targets", nargs="*", metavar="TARGET",
                        help="module names or .lean files (default: all of the project's files)")
    parser.add_argument("--check", action="store_true",
                        help="download nothing; exit 1 if a needed file is missing")
    parser.add_argument("--dir", metavar="FOLDER", help="the project folder (default: this one)")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="show the download tool's own output")
    args = parser.parse_args(argv)

    try:
        root = find_project_root(Path(args.dir).resolve() if args.dir else Path.cwd())
        ws = Workspace(root)
        targets = [as_module(root, t) for t in args.targets] or project_modules(root)
        needed, ask = needed_files(ws, targets)

        def missing() -> List[str]:
            return sorted(m for m, source_root in needed.items()
                          if not ws.olean(source_root, m).is_file())

        version = ws.mathlib_version()
        try:
            downloaded_for = ws.stamp.read_text(encoding="utf-8").strip()
        except OSError:
            downloaded_for = None
        changed = downloaded_for is not None and downloaded_for != version
        absent = missing()
        from_mathlib = sum(1 for m in needed if needed[m] == ws.mathlib)
        what = "%d prebuilt files needed (%d from Mathlib, %d from the packages it uses)" % (
            len(needed), from_mathlib, len(needed) - from_mathlib)

        if args.check:
            if changed:
                say("Mathlib files: Mathlib or Lean changed version since the files were "
                    "downloaded. Run this script without --check before building.")
                return 1
            if absent:
                say("Mathlib files: %d of the %s are missing, for example %s. "
                    "Run this script without --check before building."
                    % (len(absent), what, ", ".join(absent[:3])))
                return 1
            say("Mathlib files: all present; %s." % what)
            return 0

        if not absent and not changed and downloaded_for is not None:
            say("Mathlib files: all present; %s." % what)
            return 0
        if not download(ws, ask, args.verbose):
            return 1
        still = missing()
        if still:
            say("Mathlib files: %d of the %s could not be downloaded, for example %s. "
                "Do not build: Lean would compile them, which takes hours."
                % (len(still), what, ", ".join(still[:3])))
            return 1
        ws.stamp.parent.mkdir(parents=True, exist_ok=True)
        ws.stamp.write_text(version + "\n", encoding="utf-8")
        if absent:
            did = "downloaded %d" % len(absent)
        elif changed:
            did = "refreshed after a version change"
        else:
            did = "confirmed with Mathlib's download tool"
        say("Mathlib files: %s; %s, all present." % (did, what))
        return 0
    except Problem as problem:
        say("get_mathlib: %s" % problem)
        return 2


if __name__ == "__main__":
    sys.exit(main())
