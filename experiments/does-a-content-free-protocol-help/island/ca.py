"""One CA bundle, for every process that has to reach a hub over TLS.

Lifted out of `run_v3.py` unchanged when the game layer needed the same
thing. It is the sort of helper that gets copied rather than shared and then
drifts, and this one cannot afford to: an agent whose MCP server has the wrong
bundle fails at the TLS handshake, with every Switchboard tool it holds
reporting an internal error -- which `PREFLIGHT.md` lists among the known
environment traps precisely because it is expensive to diagnose from the
symptom.

The concatenation is the point. A managed hub reached through an agent proxy
needs the proxy's certificate *and* the system roots, and no single file on
disk has both.
"""

from __future__ import annotations

import glob
import os
import re
from pathlib import Path

_CERT = re.compile(
    r"-----BEGIN CERTIFICATE-----.*?-----END CERTIFICATE-----", re.S)


def bundle(dest: Path) -> str:
    """Write every certificate we can find to `dest`, and return its path.

    Duplicates are dropped in first-seen order rather than sorted, so a
    rebuild produces the same file and nothing downstream sees a change that
    is not one.
    """
    found: list[str] = []
    for name in [*sorted(glob.glob("/etc/ssl/certs/*.pem")),
                 os.environ.get("SSL_CERT_FILE", ""),
                 "/root/.ccr/ca-bundle.crt"]:
        if not name:
            continue
        try:
            text = Path(name).read_text()
        except OSError:
            continue
        found += _CERT.findall(text)
    seen: set[str] = set()
    keep = [c for c in found if not (c in seen or seen.add(c))]
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text("\n".join(keep) + "\n")
    return str(dest)
