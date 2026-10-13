"""Regression tests for the clinically defined Duke Treadmill Score."""
import csv
import json
import math

import pytest

from duke import calculate_score, assess_row, process_csv, main


@pytest.mark.parametrize("minutes,st,angina,expected,tier", [
    (12, 0, 0, 12, "low"),
    (9, 1, 1, 0, "moderate"),
    (4, 2, 2, -14, "high"),
    (5, 0, 0, 5, "low"),
    (4.99, 0, 0, 4.99, "moderate"),
    (0, 2, 0, -10, "moderate"),
    (0, 2.002, 0, -10.01, "high"),
    (10.5, 0.5, 2, 0, "moderate"),
])
def test_reference_formula_and_risk_boundaries(minutes, st, angina, expected, tier):
    result = calculate_score({
        "exercise_minutes": minutes,
        "st_deviation_mm": st,
        "angina_index": angina,
    })
    assert result["score"] == pytest.approx(expected)
    assert result["tier"] == tier
    assert result["detail"]["st_penalty"] == pytest.approx(5 * st)
    assert result["detail"]["angina_penalty"] == 4 * angina


@pytest.mark.parametrize("data", [
    {},
    {"Smoking": True},
    {"exercise_minutes": 5, "st_deviation_mm": 0},
    {"exercise_minutes": -1, "st_deviation_mm": 0, "angina_index": 0},
    {"exercise_minutes": 5, "st_deviation_mm": -1, "angina_index": 0},
    {"exercise_minutes": math.nan, "st_deviation_mm": 0, "angina_index": 0},
    {"exercise_minutes": 5, "st_deviation_mm": math.inf, "angina_index": 0},
    {"exercise_minutes": True, "st_deviation_mm": 0, "angina_index": 0},
    {"exercise_minutes": 5, "st_deviation_mm": 0, "angina_index": True},
    {"exercise_minutes": 5, "st_deviation_mm": 0, "angina_index": 3},
    {"exercise_minutes": 5, "st_deviation_mm": 0, "angina_index": 1.5},
    "not a dictionary",
    None,
])
def test_invalid_values_rejected(data):
    with pytest.raises(ValueError):
        calculate_score(data)


def test_csv_field_normalization_and_validation():
    result = assess_row({
        "Exercise Minutes": "9.5",
        "ST-Deviation-mm": "0.5",
        "ANGINA_INDEX": "1",
        "patient_id": "RECORD-1",
    })
    assert result["score"] == pytest.approx(3.0)
    with pytest.raises(ValueError, match="missing required"):
        assess_row({"patient_id": "RECORD-1"})


def test_batch_csv_and_formula_injection(tmp_path):
    source = tmp_path / "input.csv"
    output = tmp_path / "output.csv"
    source.write_text(
        "patient_id,exercise_minutes,st_deviation_mm,angina_index\n"
        "=2+2,12,0,0\n"
        "P002,4,2,2\n", encoding="utf-8"
    )
    rows = process_csv(str(source), str(output))
    assert len(rows) == 2
    assert rows[0]["score"] == 12
    assert rows[1]["tier"] == "high"
    with output.open(newline="", encoding="utf-8") as stream:
        exported = list(csv.DictReader(stream))
    assert exported[0]["patient_id"] == "'=2+2"
    assert exported[0]["score"] == "12.0"
    assert json.loads(exported[1]["detail"])["angina_index"] == 2


def test_batch_failure_does_not_create_output(tmp_path):
    source = tmp_path / "bad.csv"
    output = tmp_path / "output.csv"
    source.write_text(
        "exercise_minutes,st_deviation_mm,angina_index\n"
        "12,0,0\n"
        "8,invalid,1\n", encoding="utf-8"
    )
    with pytest.raises(ValueError, match="row 3"):
        process_csv(str(source), str(output))
    assert not output.exists()


def test_batch_validation(tmp_path):
    with pytest.raises(ValueError):
        process_csv("", "out.csv")
    with pytest.raises(ValueError):
        process_csv("in.csv", "")
    with pytest.raises(FileNotFoundError):
        process_csv(str(tmp_path / "missing.csv"), str(tmp_path / "out.csv"))


def test_cli_single_and_errors(capsys):
    assert main(["single", "--exercise-minutes", "9",
                 "--st-deviation-mm", "1", "--angina-index", "1"]) == 0
    assert json.loads(capsys.readouterr().out)["score"] == 0
    assert main(["single", "--json",
                 '{"exercise_minutes":12,"st_deviation_mm":0,"angina_index":0}']) == 0
    assert json.loads(capsys.readouterr().out)["tier"] == "low"
    assert main(["single", "--json", "not json"]) == 1
    assert main(["single", "--exercise-minutes", "10"]) == 1
    assert main(["single", "--json",
                 '{"exercise_minutes":4,"st_deviation_mm":0,"angina_index":0}',
                 "--exercise-minutes", "5"]) == 1


def test_cli_batch(tmp_path):
    source = tmp_path / "input.csv"
    target = tmp_path / "output.csv"
    source.write_text("exercise_minutes,st_deviation_mm,angina_index\n12,0,0\n",
                      encoding="utf-8")
    assert main(["batch", "--input", str(source), "--output", str(target)]) == 0
    assert target.exists()
    assert main(["batch", "--input", "nonexistent.csv", "--output", str(target)]) == 1
