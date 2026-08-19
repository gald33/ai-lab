"""Put the experiment's own package on the path for pytest.

The experiment owns its code rather than importing a shared framework, so
`barter` is a package sitting next to this file rather than an installed
distribution.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
