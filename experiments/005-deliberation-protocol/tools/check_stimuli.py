"""Fail if a frozen stimulus has moved.

The placebo carries the causal weight of 005, so a wording revision after the
pilot is not a tidy-up — it is a different experiment wearing the old
pre-registration. This recomputes both hashes against `PREREGISTRATION.md` and
is run by the gates, so editing a stimulus breaks the suite loudly.
"""

from __future__ import annotations

import hashlib
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent


def frozen() -> dict[str, str]:
    text = (ROOT / "PREREGISTRATION.md").read_text()
    out = {}
    for name in ("protocol.md", "placebo.md"):
        m = re.search(rf"`stimuli/{re.escape(name)}`\s*\|\s*`([0-9a-f]{{64}})`", text)
        if not m:
            raise AssertionError(f"no frozen hash recorded for {name}")
        out[name] = m.group(1)
    return out


def check() -> list[str]:
    problems = []
    for name, want in frozen().items():
        path = ROOT / "stimuli" / name
        if not path.exists():
            problems.append(f"{name}: missing")
            continue
        got = hashlib.sha256(path.read_bytes()).hexdigest()
        if got != want:
            problems.append(f"{name}: frozen {want[:12]}… but file is {got[:12]}…")
    return problems


if __name__ == "__main__":
    bad = check()
    for line in bad:
        print(line)
    print("stimuli unchanged" if not bad else "STIMULI HAVE MOVED")
    sys.exit(1 if bad else 0)
