"""Make the vendored client importable without installing Home Assistant.

`koolnova_api` lives inside `custom_components/koolnova/` and is normally imported
relatively by the integration. The tests import it as a top-level package, which is
why this file puts that directory on `sys.path`.

Importing `custom_components.koolnova` itself would pull in Home Assistant, so the
tests deliberately reach only into `koolnova_api`, which depends on `requests` alone.
"""

import sys
from pathlib import Path

_CLIENT_PARENT = Path(__file__).resolve().parent.parent / "custom_components" / "koolnova"

if str(_CLIENT_PARENT) not in sys.path:
    sys.path.insert(0, str(_CLIENT_PARENT))
