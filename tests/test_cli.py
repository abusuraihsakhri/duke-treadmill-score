"""Regression coverage for legacy audit CSV import."""
import csv

import pytest

from cli import _parse_csv_bool, main


@pytest.mark.parametrize("value,expected", [
    ("False", False), ("false", False), ("0", False),
    ("no", False), ("", False), (None, False),
    ("True", True), ("1", True), ("yes", True),
])
def test_boolean_parsing(value, expected):
    assert _parse_csv_bool(value) is expected


def test_invalid_boolean_rejected():
    with pytest.raises(ValueError):
        _parse_csv_bool("not sure")


def test_false_flag_stays_routine_in_batch(tmp_path):
    source = tmp_path / "records.csv"
    destination = tmp_path / "output.csv"
    source.write_text(
        "task_id,target_identifier,primary_metric,secondary_metric,status_descriptor,is_critical_flag\n"
        "T-001,KEY-001,10,2,NOMINAL,False\n", encoding="utf-8"
    )
    assert main(["batch", "-i", str(source), "-o", str(destination)]) == 0
    with destination.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert rows[0]["overall_urgency"] == "ROUTINE"
