#!/usr/bin/env python3
"""Print the grounding bundle for exactly one experiment.

    tools/ground.py 004            # what an agent working on 004 may carry
    tools/ground.py 004 --paths    # just the paths, one per line
    tools/ground.py 004 --new-run "consumption sweep"

The point is the *exactly one* part. An agent running an experiment is grounded
in the repo-root standing decisions, the general grounding, and that
experiment's own documents — and in no other experiment's. See
experiments/GROUNDING.md.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXPERIMENTS = ROOT / "experiments"
TEMPLATE = ROOT / "templates" / "experiment" / "runs" / "RUN-TEMPLATE.md"

# Read in this order. Everything else in the experiment directory is reachable
# from its CLAUDE.md; nothing outside it is in scope.
GENERAL = ["CLAUDE.md", "experiments/GROUNDING.md"]


def find(ident: str) -> Path:
    matches = sorted(
        d for d in EXPERIMENTS.iterdir()
        if d.is_dir() and (d.name == ident or d.name.startswith(f"{ident}-"))
    )
    if not matches:
        sys.exit(f"no experiment matches {ident!r} in {EXPERIMENTS}")
    if len(matches) > 1:
        sys.exit(f"{ident!r} is ambiguous: {', '.join(d.name for d in matches)}")
    return matches[0]


def bundle(exp: Path) -> list[Path]:
    paths = [ROOT / p for p in GENERAL]
    paths.append(exp / "CLAUDE.md")
    return paths


def next_run_number(runs: Path) -> int:
    used = [
        int(m.group(1))
        for f in runs.glob("*.md")
        if (m := re.match(r"(\d+)-", f.name))
    ]
    return max(used, default=0) + 1


def slugify(text: str) -> str:
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", text.lower())).strip("-")


def new_run(exp: Path, name: str) -> Path:
    if not TEMPLATE.exists():
        sys.exit(f"missing run template at {TEMPLATE}")
    runs = exp / "runs"
    runs.mkdir(exist_ok=True)
    number = next_run_number(runs)
    path = runs / f"{number:03d}-{slugify(name)}.md"
    if path.exists():
        sys.exit(f"{path} already exists")
    body = TEMPLATE.read_text().replace(
        "# Run NNN — <short name>", f"# Run {number:03d} — {name}", 1
    )
    path.write_text(body)
    return path


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("experiment", help="number or directory name, e.g. 004")
    ap.add_argument("--paths", action="store_true", help="print paths only")
    ap.add_argument("--new-run", metavar="NAME", help="open a run record from the template")
    args = ap.parse_args()

    exp = find(args.experiment)

    if args.new_run:
        path = new_run(exp, args.new_run)
        print(f"opened {path.relative_to(ROOT)}")
        print("Fill in specification, assumptions and hypothesis, and commit")
        print("it before the run starts.")
        return 0

    paths = bundle(exp)
    missing = [p for p in paths if not p.exists()]

    if args.paths:
        for p in paths:
            print(p.relative_to(ROOT))
        return 1 if missing else 0

    for p in paths:
        rel = p.relative_to(ROOT)
        if not p.exists():
            print(f"\n===== {rel} — MISSING =====\n")
            continue
        print(f"\n===== {rel} =====\n")
        print(p.read_text().rstrip())

    runs = sorted((exp / "runs").glob("[0-9]*.md"))
    print(f"\n===== {(exp / 'runs').relative_to(ROOT)} =====\n")
    if runs:
        for r in runs:
            first = r.read_text().splitlines()[0].lstrip("# ").strip()
            print(f"  {r.name}  {first}")
    else:
        print("  no run records yet — open one before running anything:")
        print(f"    tools/ground.py {args.experiment} --new-run \"<name>\"")

    print(f"\nIn scope: the above, and what {(exp / 'CLAUDE.md').relative_to(ROOT)}")
    print("points at. No other experiments/ directory.")

    if missing:
        print("\nmissing: " + ", ".join(str(p.relative_to(ROOT)) for p in missing))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
