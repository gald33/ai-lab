#!/usr/bin/env python3
"""Print the grounding bundle for exactly one experiment.

    tools/ground.py ruin              # what an agent working on it may carry
    tools/ground.py ruin --paths      # just the paths, one per line
    tools/ground.py ruin --preflight  # just the gates, before spending
    tools/ground.py ruin --new-run "consumption sweep"

An experiment is named by its question, so any distinctive part of that
question finds it: `ruin`, `stock`, and the full
`is-ruin-the-convention-or-the-commitment` all reach the same directory.

**Retired numbers still resolve, and say so.** Every experiment was numbered
once, those numbers are cited in reports and run records that are not being
rewritten, and a lookup that failed on `004` would send the reader to grep. So
`004` works and prints the name it is now, on stderr, where it does not
pollute a `--paths` pipe. See experiments/README.md.

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

#: The number each experiment used to carry, and the directory it is now. Kept
#: because ~1,200 citations in reports and run records still say "005", and
#: those documents are the record and are not being rewritten to look as though
#: they always said something else. Two entries share `006`, which is the
#: measured reason the number was never an identifier: see experiments/README.md.
RETIRED_NUMBERS = {
    "001": "is-coordination-less-to-reason-about",
    "002": "which-part-of-a-convention-works",
    "003": "which-promotion-rule-beats-luck",
    "004": "is-ruin-the-convention-or-the-commitment",
    "005": "does-a-content-free-protocol-help",
    "007": "do-they-take-a-handed-over-answer",
}

#: `006` was two experiments at once. It resolves to neither, and says both.
AMBIGUOUS_NUMBERS = {
    "006": ("can-an-agent-hold-availability",
            "does-telling-traders-what-to-disclose-help"),
}


def find(ident: str) -> Path:
    """The one experiment `ident` names, by name, by fragment, or by old number.

    Fragment matching is deliberate: an experiment is named by its question, and
    nobody types `is-ruin-the-convention-or-the-commitment`. Ambiguity is an
    error rather than a first match, because silently grounding an agent in the
    wrong experiment is the contamination GROUNDING.md exists to prevent.
    """
    if ident in AMBIGUOUS_NUMBERS:
        names = AMBIGUOUS_NUMBERS[ident]
        sys.exit(
            f"{ident!r} was two experiments at once, which is why experiments "
            f"are no longer numbered. Name one: {', '.join(names)}"
        )

    if ident in RETIRED_NUMBERS:
        name = RETIRED_NUMBERS[ident]
        print(f"{ident} is now {name}", file=sys.stderr)
        ident = name

    directories = sorted(d for d in EXPERIMENTS.iterdir() if d.is_dir())

    exact = [d for d in directories if d.name == ident]
    if exact:
        return exact[0]

    matches = [d for d in directories if ident in d.name]
    if not matches:
        sys.exit(
            f"no experiment matches {ident!r} in {EXPERIMENTS}\n"
            + "\n".join(f"  {d.name}" for d in directories)
        )
    if len(matches) > 1:
        sys.exit(f"{ident!r} is ambiguous: {', '.join(d.name for d in matches)}")
    return matches[0]


def bundle(exp: Path) -> list[Path]:
    paths = [ROOT / p for p in GENERAL]
    paths.append(exp / "CLAUDE.md")
    paths.append(exp / "PREFLIGHT.md")
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
    ap.add_argument("experiment",
                    help="any distinctive part of the experiment's question, "
                         "e.g. 'ruin'. A retired number still resolves.")
    ap.add_argument("--paths", action="store_true", help="print paths only")
    ap.add_argument("--new-run", metavar="NAME", help="open a run record from the template")
    ap.add_argument("--preflight", action="store_true",
                    help="print only this experiment's gates, before spending")
    args = ap.parse_args()

    exp = find(args.experiment)

    if args.preflight:
        path = exp / "PREFLIGHT.md"
        if not path.exists():
            print(f"{path.relative_to(ROOT)} — MISSING")
            print("Declare the gates before spending. Start from")
            print("templates/experiment/PREFLIGHT.md.")
            return 1
        print(path.read_text().rstrip())
        print("\nThis prints the gates; it does not run them. Record every")
        print("result, with the commit it ran on, in the run record.")
        return 0

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
