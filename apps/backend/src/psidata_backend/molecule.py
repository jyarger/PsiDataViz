"""Resolve a SMILES string or a compound name to a 3D structure for the molecular viewer.

SMILES are embedded into 3D coordinates with RDKit; names (common or IUPAC) are first resolved to a
SMILES via the public PubChem PUG REST API. The result is an MDL mol block that 3Dmol.js renders.
"""

from __future__ import annotations

import urllib.parse

import httpx

_PUBCHEM = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"


def smiles_to_molblock(smiles: str) -> str:
    """Embed a SMILES string into an optimized 3D MDL mol block (falls back to 2D if embedding fails)."""
    from rdkit import Chem
    from rdkit.Chem import AllChem

    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise ValueError(f"Could not parse SMILES: {smiles!r}")
    mol = Chem.AddHs(mol)
    if AllChem.EmbedMolecule(mol, randomSeed=0xF00D) == 0:
        try:
            AllChem.MMFFOptimizeMolecule(mol)
        except Exception:  # noqa: BLE001  optimization is best-effort
            pass
    else:
        AllChem.Compute2DCoords(mol)  # embedding failed (e.g. odd valences) — show a flat layout
    return Chem.MolToMolBlock(mol)


def resolve_name(name: str) -> dict:
    """Resolve a compound name (common or IUPAC) to SMILES + canonical info via PubChem."""
    quoted = urllib.parse.quote(name.strip())
    url = f"{_PUBCHEM}/compound/name/{quoted}/property/CanonicalSMILES,IUPACName,MolecularFormula/JSON"
    resp = httpx.get(url, timeout=12.0, follow_redirects=True)
    if resp.status_code == 404:
        raise ValueError(f"No compound found for {name!r}")
    resp.raise_for_status()
    props = resp.json()["PropertyTable"]["Properties"][0]
    smiles = next((v for k, v in props.items() if "SMILES" in k), None)
    if not smiles:
        raise ValueError(f"PubChem returned no SMILES for {name!r}")
    return {"smiles": smiles, "iupac": props.get("IUPACName"),
            "formula": props.get("MolecularFormula"), "cid": props.get("CID")}


def molecule_payload(*, smiles: str | None = None, name: str | None = None,
                     q: str | None = None) -> dict:
    """Build the viewer payload from a SMILES string, a compound name, or a free-text ``q`` that is tried
    as SMILES first (offline) and otherwise resolved as a name via PubChem."""
    from rdkit import Chem

    resolved: dict = {}
    if q:
        q = q.strip()
        if Chem.MolFromSmiles(q) is not None:
            smiles = q
        else:
            name = q
    if name and not smiles:
        resolved = resolve_name(name)
        smiles = resolved["smiles"]
    if not smiles:
        raise ValueError("provide either a SMILES string or a compound name")
    return {
        "molblock": smiles_to_molblock(smiles),
        "smiles": smiles,
        "query": q or name or smiles,
        "iupac": resolved.get("iupac"),
        "formula": resolved.get("formula"),
        "cid": resolved.get("cid"),
    }
