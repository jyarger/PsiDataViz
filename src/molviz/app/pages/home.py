"""Home page: point at a public GitHub repo and scan it into a catalog."""

from __future__ import annotations

import dash
import dash_mantine_components as dmc
from dash import Input, Output, State, callback, dcc, no_update

from molviz.app.services import scan_repo

dash.register_page(__name__, path="/", name="Home")

DEFAULT_REPO = "https://github.com/yargerlab/Data"


def layout(**_kwargs):
    return dmc.Stack(
        [
            dmc.Title("Point at a data repository", order=2),
            dmc.Text(
                "Paste a public GitHub repo that stores molecular-science data in per-instrument "
                "folders (e.g. DSC/, FTIR/, NMR/). MolViz scans it and summarizes what it finds.",
                c="dimmed",
            ),
            dmc.Group(
                [
                    dmc.TextInput(
                        id="repo-input",
                        value=DEFAULT_REPO,
                        placeholder="owner/repo or https://github.com/owner/repo",
                        label="GitHub repository",
                        style={"flex": 1, "minWidth": 360},
                    ),
                    dmc.Button("Scan repository", id="scan-btn", mt=25),
                ],
                align="flex-end",
            ),
            dcc.Loading(dash.html.Div(id="scan-output"), type="dot"),
        ],
        gap="md",
    )


@callback(
    Output("repo-url", "data"),
    Output("scan-output", "children"),
    Input("scan-btn", "n_clicks"),
    State("repo-input", "value"),
    prevent_initial_call=True,
)
def on_scan(_clicks, url):
    if not url or not url.strip():
        return no_update, dmc.Alert("Please enter a repository URL.", color="yellow")
    try:
        catalog = scan_repo(url.strip())
    except Exception as exc:  # noqa: BLE001 - surface any failure to the user
        return no_update, dmc.Alert(f"Could not scan {url!r}: {exc}", color="red",
                                    title="Scan failed")

    summary = catalog.summary()
    groups = summary["groups"]
    badges = [
        dmc.Badge(
            f"{tech} · {info['n_supported']}/{info['n_files']}",
            variant="filled" if info["n_supported"] else "light",
            color="blue" if info["n_supported"] else "gray",
            size="lg",
        )
        for tech, info in sorted(groups.items(), key=lambda kv: (-kv[1]["n_supported"], kv[0]))
    ]
    body = dmc.Stack(
        [
            dmc.Text(
                f"Found {summary['n_files']} files across {len(groups)} folders — "
                f"{summary['n_supported']} are visualizable with current readers.",
                fw=600,
            ),
            dmc.Text("Folders (supported / total):", size="sm", c="dimmed"),
            dmc.Group(badges, gap="xs"),
            dcc.Link(dmc.Button("Browse datasets →", mt="sm"), href="/browse"),
        ],
        gap="xs",
    )
    return url.strip(), dmc.Paper(body, p="md", withBorder=True, radius="md", mt="sm")
