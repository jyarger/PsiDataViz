"""Built-in readers. Importing a reader module registers it via ``@register_reader``.

To add a technique, create a module here (e.g. ``ftir_jcamp.py``) and import it below.
"""

from __future__ import annotations

from . import (
    comp_log,  # noqa: F401  (import triggers registration)
    comp_spectrum,  # noqa: F401  (import triggers registration)
    dsc_trios,  # noqa: F401  (import triggers registration)
    ftir_jcamp,  # noqa: F401  (import triggers registration)
    ftir_opus,  # noqa: F401  (import triggers registration)
    ftir_pe_asc,  # noqa: F401  (import triggers registration)
    ftir_text,  # noqa: F401  (import triggers registration)
    nmr_jcamp,  # noqa: F401  (import triggers registration)
    nmr_text,  # noqa: F401  (import triggers registration)
    nmr_totxt,  # noqa: F401  (import triggers registration)
    raman_text,  # noqa: F401  (import triggers registration)
    structure_file,  # noqa: F401  (import triggers registration)
    tga_text,  # noqa: F401  (import triggers registration)
    uvvis_text,  # noqa: F401  (import triggers registration)
    xrd_image,  # noqa: F401  (import triggers registration)
    xrd_panalytical,  # noqa: F401  (import triggers registration)
    xrd_text,  # noqa: F401  (import triggers registration)
)

__all__ = ["comp_log", "comp_spectrum", "dsc_trios", "ftir_jcamp", "ftir_opus", "ftir_pe_asc",
           "ftir_text", "nmr_jcamp", "nmr_text", "nmr_totxt", "raman_text", "structure_file",
           "tga_text", "uvvis_text", "xrd_image", "xrd_panalytical", "xrd_text"]
