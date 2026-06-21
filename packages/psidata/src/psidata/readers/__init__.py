"""Built-in readers. Importing a reader module registers it via ``@register_reader``.

To add a technique, create a module here (e.g. ``ftir_jcamp.py``) and import it below.
"""

from __future__ import annotations

from . import (
    dsc_trios,  # noqa: F401  (import triggers registration)
    ftir_text,  # noqa: F401  (import triggers registration)
    nmr_jcamp,  # noqa: F401  (import triggers registration)
    raman_text,  # noqa: F401  (import triggers registration)
)

__all__ = ["dsc_trios", "ftir_text", "nmr_jcamp", "raman_text"]
