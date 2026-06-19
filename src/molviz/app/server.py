"""Dash application factory + entrypoint.

The app is a thin shell: a header with navigation, two session-scoped ``dcc.Store``s that carry
the current repo URL and dataset selection across pages, and a page container. All real work lives
in :mod:`molviz.app.services`, :mod:`molviz.app.plotting`, and the core library.
"""

from __future__ import annotations

import os

import dash
import dash_mantine_components as dmc
from dash import Dash, dcc

BRAND = "MolViz"
TAGLINE = "Visualize Experimental & Computational Molecular Science Data"

_NAV = [("Home", "/"), ("Browse", "/browse"), ("Visualize", "/visualize")]


def _header() -> dmc.Paper:
    links = [
        dcc.Link(
            label,
            href=href,
            style={"textDecoration": "none", "color": "#1c7ed6", "fontWeight": 600,
                   "padding": "4px 10px"},
        )
        for label, href in _NAV
    ]
    return dmc.Paper(
        dmc.Group(
            [
                dmc.Group(
                    [
                        dmc.ThemeIcon("🧪", size="lg", variant="light", radius="md"),
                        dmc.Stack(
                            [
                                dmc.Title(BRAND, order=3, m=0),
                                dmc.Text(TAGLINE, size="xs", c="dimmed"),
                            ],
                            gap=0,
                        ),
                    ],
                    gap="sm",
                ),
                dmc.Group(links, gap="xs"),
            ],
            justify="space-between",
            align="center",
        ),
        p="md",
        shadow="xs",
        radius=0,
        withBorder=True,
    )


def create_app() -> Dash:
    app = Dash(
        __name__,
        use_pages=True,
        suppress_callback_exceptions=True,
        title=BRAND,
        update_title=None,
    )
    app.layout = dmc.MantineProvider(
        forceColorScheme="light",
        children=[
            dcc.Store(id="repo-url", storage_type="session"),
            dcc.Store(id="selection", storage_type="session"),
            _header(),
            dmc.Container(dash.page_container, size="xl", py="lg"),
        ],
    )
    return app


app = create_app()
server = app.server  # WSGI entrypoint for gunicorn


def main() -> None:
    app.run(
        host=os.environ.get("HOST", "127.0.0.1"),
        port=int(os.environ.get("PORT", "8050")),
        debug=os.environ.get("MOLVIZ_DEBUG", "") in ("1", "true", "True"),
    )


if __name__ == "__main__":
    main()
