"""
Tests for duke.py core scoring module.
"""
import sys
from pathlib import Path
import tempfile
import os
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
import duke as m


def test_score():
    r = m.calculate_score({'age': 68, 'sex': 'M', 'cancer': 1})
    assert 'score' in r and 'tier' in r
    r2 = m.calculate_score({'age': 30, 'sex': 'F'})
    assert r2['score'] <= r['score']


def test_calculate_score_empty():
    """Empty dict should return score 0 and low tier."""
    r = m.calculate_score({})
    assert r['score'] == 0
    assert r['tier'] == 'low'
    assert r['detail'] == {}


def test_calculate_score_all_factors():
    """All factors present should return max score."""
    present = {name: True for name, _ in m.FACTORS}
    r = m.calculate_score(present)
    expected_score = sum(w for _, w in m.FACTORS)
    assert r['score'] == expected_score
    assert r['tier'] == 'high'


def test_calculate_score_various_inputs():
    """Test various truthy/falsy input formats."""
    # Test with 1/0
    r1 = m.calculate_score({'Smoking': 1, 'Hypertension': 0})
    assert r1['score'] == 1
    # Test with yes/no
    r2 = m.calculate_score({'Smoking': 'yes', 'Hypertension': 'no'})
    assert r2['score'] == 1
    # Test with true/false strings
    r3 = m.calculate_score({'Smoking': 'true', 'Hypertension': 'false'})
    assert r3['score'] == 1


def test_calculate_score_invalid_input():
    """Non-dict input should raise ValueError."""
    with pytest.raises(ValueError):
        m.calculate_score("not a dict")
    with pytest.raises(ValueError):
        m.calculate_score(None)
    with pytest.raises(ValueError):
        m.calculate_score([1, 2, 3])


def test_calculate_score_tiers():
    """Test tier thresholds."""
    # Low tier (score <= 2)
    r_low = m.calculate_score({'Smoking': 1})
    assert r_low['tier'] == 'low'
    # Moderate tier (score <= 4)
    r_mod = m.calculate_score({'Smoking': 1, 'Hypertension': 1, 'Diabetes': 1})
    assert r_mod['tier'] == 'moderate'
    # High tier (score > 4)
    r_high = m.calculate_score({name: 1 for name, _ in m.FACTORS})
    assert r_high['tier'] == 'high'


def test_assess_row():
    """Test CSV row assessment."""
    row = {'Smoking': '1', 'Hypertension': '0', 'Diabetes': 'yes'}
    r = m.assess_row(row)
    assert r['score'] == 2


def test_assess_row_invalid():
    """Non-dict row should raise ValueError."""
    with pytest.raises(ValueError):
        m.assess_row("not a dict")


def test_process_csv():
    """Test CSV batch processing."""
    # Create a temp input file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as f:
        f.write("patient_id,Smoking,Hypertension,Diabetes\n")
        f.write("P001,1,0,1\n")
        f.write("P002,0,1,0\n")
        inp = f.name
    out = inp + '.out.csv'
    try:
        results = m.process_csv(inp, out)
        assert len(results) == 2
        assert results[0]['score'] == 2
        assert results[1]['score'] == 1
        # Verify output file exists
        assert os.path.exists(out)
    finally:
        os.unlink(inp)
        if os.path.exists(out):
            os.unlink(out)


def test_process_csv_file_not_found():
    """Missing input file should raise FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        m.process_csv('nonexistent_file.csv', 'output.csv')


def test_process_csv_invalid_paths():
    """Invalid paths should raise ValueError."""
    with pytest.raises(ValueError):
        m.process_csv('', 'output.csv')
    with pytest.raises(ValueError):
        m.process_csv('input.csv', '')
    with pytest.raises(ValueError):
        m.process_csv(None, 'output.csv')


def test_main_single():
    """Test CLI single command."""
    assert m.main(['single', '--smoking', '1']) == 0


def test_main_single_json():
    """Test CLI single command with JSON."""
    assert m.main(['single', '--json', '{"Smoking": true}']) == 0


def test_main_single_invalid_json():
    """Test CLI single command with invalid JSON."""
    assert m.main(['single', '--json', 'not valid json']) == 1


def test_main_batch():
    """Test CLI batch command."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as f:
        f.write("patient_id,Smoking\n")
        f.write("P001,1\n")
        inp = f.name
    out = inp + '.out.csv'
    try:
        assert m.main(['batch', '--input', inp, '--output', out]) == 0
    finally:
        os.unlink(inp)
        if os.path.exists(out):
            os.unlink(out)


def test_main_batch_missing_file():
    """Test CLI batch command with missing file."""
    assert m.main(['batch', '--input', 'nonexistent.csv', '--output', 'out.csv']) == 1
