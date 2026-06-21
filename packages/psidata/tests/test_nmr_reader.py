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


# A tiny hand-encoded (X++(Y..Y)) block exercising SQZ / DIF(+,-,0) / DUP.
# "6A0Lk%UN" -> leadX=6, ordinates [10, 13, 11, 11, 11, 11, 16].
_ASDF = (
    "##TITLE=synthetic compressed\n##JCAMP-DX=5.01\n##DATA TYPE= NMR SPECTRUM\n"
    "##.OBSERVE NUCLEUS= ^13C\n##.OBSERVE FREQUENCY= 125.0\n"
    "##XUNITS=HZ\n##XFACTOR=1\n##YFACTOR=1\n##FIRSTX=0\n##LASTX=6\n"
    "##NPOINTS=7\n##FIRSTY=10\n##XYDATA=(X++(Y..Y))\n6A0Lk%UN\n##END=\n"
)


def test_decodes_compressed_asdf():
    ds = read(Candidate(filename="bruker.jdx", text=_ASDF))
    assert ds.technique == "NMR"
    sig = ds.signals[0]
    assert sig.npoints == 7
    assert list(sig.frame["Intensity"]) == [10, 13, 11, 11, 11, 11, 16]
    assert list(sig.frame["Frequency"]) == [6, 5, 4, 3, 2, 1, 0]
    assert sig.x.unit == "Hz"
    assert ds.metadata.nucleus == "13C"


def test_asdf_rejects_mismatched_npoints():
    # validation guard: a decode that disagrees with the header must raise, not emit wrong data
    bad = _ASDF.replace("##NPOINTS=7", "##NPOINTS=99")
    with pytest.raises(ValueError, match="NPOINTS"):
        read(Candidate(filename="bruker.jdx", text=bad))
