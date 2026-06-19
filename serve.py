"""Run the MolViz dev server without relying on an editable install:

    python serve.py

Injects ``src/`` onto the path, then starts the Dash app. Handy on machines where the
interpreter doesn't honor editable-install ``.pth`` files. For production, use gunicorn against
``molviz.app.server:server`` (see docs/deploy.md).
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from molviz.app.server import main  # noqa: E402

if __name__ == "__main__":
    main()
