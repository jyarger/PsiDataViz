from __future__ import annotations

from psidata import Candidate, compare_datasets, read


def test_same_dsc_data_as_tab_vs_comma_is_identical(dsc_txt):
    # The user's exact scenario: same DSC run saved as tab-delimited .txt and comma-delimited .csv.
    tab = read(Candidate(filename="run.txt", text=dsc_txt))
    comma = read(Candidate(filename="run.csv", text=dsc_txt.replace("\t", ",")))
    result = compare_datasets(tab, comma, a_label=".txt", b_label=".csv")
    assert result.identical, result.differences
    assert result.summary == "identical data"


def test_different_runs_report_differences(dsc_txt, dsc_csv):
    a = read(Candidate(filename="indium.txt", text=dsc_txt))        # 2 segments
    b = read(Candidate(filename="acetaminophen.csv", text=dsc_csv))  # 5 segments
    result = compare_datasets(a, b)
    assert not result.identical
    assert any("signal count" in d for d in result.differences)


def test_numeric_difference_is_detected(dsc_txt):
    a = read(Candidate(filename="run.txt", text=dsc_txt))
    b = read(Candidate(filename="run.txt", text=dsc_txt))
    # perturb one heat-flow value in b
    ycol = b.signals[0].y.label
    b.signals[0].frame.loc[0, ycol] = b.signals[0].frame.loc[0, ycol] + 5.0
    result = compare_datasets(a, b)
    assert not result.identical
    assert any("max abs diff" in d for d in result.differences)
