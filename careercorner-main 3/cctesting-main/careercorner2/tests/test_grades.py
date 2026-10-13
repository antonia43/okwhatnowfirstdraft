import pytest

from utils.grades import (
    calculate_cif, compare_with_cutoff, format_grade, guess_scale,
    merge_grades_data, normalize_grades_data, to_20, to_200,
)


def sample():
    return {
        "track": "Sciences",
        "current_year": "12th Grade (Completed)",
        "grades": {
            "10th": {"Port": 16, "Math": 18},
            "11th": {"Port": 17, "Math": 18},
            "12th": {"Port": 17, "Math": 18},
            "exams": {"Math A": 180, "Port": 160},
        },
    }


def test_conversions():
    assert to_200(17.8) == pytest.approx(178.0)
    assert to_20(138.5) == pytest.approx(13.85)
    assert to_20(13.85, 20) == pytest.approx(13.85)
    assert to_200(150, 200) == 150
    assert guess_scale(17.2) == 20 and guess_scale(138.5) == 200


def test_out_of_range():
    with pytest.raises(ValueError):
        to_200(25, 20)
    with pytest.raises(ValueError):
        to_20(-1)
    with pytest.raises(ValueError):
        to_20(250)


def test_format():
    assert format_grade(138.5) == "138.5/200 (13.85/20)"


def test_cif_standard():
    r = calculate_cif(sample())
    assert r["secondary_average_20"] == pytest.approx(17.33, abs=0.01)
    assert r["exam_average_200"] == 170
    assert r["cif_200"] == pytest.approx(173.33 * 0.65 + 170 * 0.35, abs=0.02)
    assert r["cif_20"] == pytest.approx(r["cif_200"] / 10, abs=0.01)


def test_cif_presets_and_custom():
    assert calculate_cif(sample(), "equal")["weights_used"] == {"secondary": 0.5, "exam": 0.5}
    assert calculate_cif(sample(), {"secondary": 0.6, "exam": 0.4})["weights_used"]["exam"] == 0.4
    with pytest.raises(ValueError):
        calculate_cif(sample(), {"secondary": 0.6, "exam": 0.6})
    with pytest.raises(ValueError):
        calculate_cif(sample(), "nope")


def test_cif_no_exams_and_10th():
    d = sample()
    d["grades"]["exams"] = {}
    assert calculate_cif(d)["weights_used"]["secondary"] == 1.0
    d = sample()
    d["current_year"] = "10th Grade"
    assert calculate_cif(d)["weights_used"]["exam"] == 0.0


def test_wrong_scale_grade_rejected():
    d = sample()
    d["grades"]["11th"]["Math"] = 150
    with pytest.raises(ValueError):
        calculate_cif(d)


def test_normalize_and_merge():
    n = normalize_grades_data({"grades": {"exams": {"Math A": 150}}})
    assert set(n["grades"]) >= {"10th", "11th", "12th", "exams"}
    assert n["student_type"] == "portuguese"
    m = merge_grades_data(sample(), {"grades": {"exams": {"Bio": 140}}, "track": ""})
    assert m["track"] == "Sciences" and m["current_year"].startswith("12th")
    assert m["grades"]["exams"]["Bio"] == 140 and m["grades"]["exams"]["Math A"] == 180


def test_compare_proposal_example():
    # GPA 17.8 (=178) vs IST 17.2 (=172) and NOVA FCT 138.5 on the 0-200 scale
    ist = compare_with_cutoff(178.0, 172.0)
    nova = compare_with_cutoff(178.0, 138.5)
    assert ist["status"] == "safe" and ist["margin_200"] == pytest.approx(6.0)
    assert nova["status"] == "safe" and nova["margin_200"] == pytest.approx(39.5)


def test_compare_bands():
    assert compare_with_cutoff(170, 172)["status"] == "target"
    assert compare_with_cutoff(177, 172)["status"] == "safe"
    assert compare_with_cutoff(166, 172)["status"] == "reach"
    for bad in (None, 0, float("nan"), ""):
        assert compare_with_cutoff(170, bad)["status"] == "unknown"
