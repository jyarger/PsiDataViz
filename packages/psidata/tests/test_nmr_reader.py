from __future__ import annotations

import pytest

from psidata import Candidate, detect, read
from psidata.readers.nmr_jcamp import JcampNmrReader, NMRMetadata


def _candidate(nmr_txt: str) -> Candidate:
    return Candidate(filename="2024_05_17_EC_Samples_1H_Adamantane_Ref.txt", text=nmr_txt,
                     uri="https://example/NMR/adamantane.txt")


def test_detects_nmr_jcamp_over_dsc(nmr_txt):
    reader = detect(_candidate(nmr_txt))
    assert reader is not None and reader.name == "nmr_jcamp"


def test_dsc_text_does_not_match_nmr(dsc_txt):
    # a DSC export must not be claimed by the NMR reader
    assert JcampNmrReader().sniff(Candidate(filename="run.txt", text=dsc_txt)) == 0.0


def test_reads_metadata(nmr_txt):
    ds = read(_candidate(nmr_txt))
    assert ds.technique == "NMR"
    assert isinstance(ds.metadata, NMRMetadata)
    m = ds.metadata
    assert m.nucleus == "1H"
    assert m.frequency_mhz == pytest.approx(399.7394556)
    assert "Adamantane" in m.sample_name


def test_parses_xy_pairs(nmr_txt):
    ds = read(_candidate(nmr_txt))
    assert len(ds.signals) == 1
    sig = ds.signals[0]
    assert sig.x.label == "Chemical shift"
    assert sig.x.unit == "ppm"
    assert sig.y.label == "Intensity"
    assert sig.npoints == 80
    # ppm axis runs high -> low in the file
    assert sig.frame["Chemical shift"].iloc[0] > sig.frame["Chemical shift"].iloc[-1]


def test_compressed_asdf_fails_loudly():
    asdf = (
        "##TITLE=compressed\n##JCAMP-DX=6.00\n##DATA TYPE= NMR SPECTRUM\n"
        "##.OBSERVE NUCLEUS=1H\n##NPOINTS=4\n##XYDATA=(X++(Y..Y))\n0 A0J1\n##END=\n"
    )
    with pytest.raises(ValueError, match="ASDF"):
        read(Candidate(filename="bruker.jdx", text=asdf))
