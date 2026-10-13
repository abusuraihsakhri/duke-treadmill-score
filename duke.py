#!/usr/bin/env python3
"""Duke Treadmill Score (DTS): clinical exercise ECG prognosis calculator.

Reference: Mark et al., NEJM 1991;325:849-853, doi:10.1056/NEJM199109193251204.
Exercise duration refers to the standard Bruce treadmill protocol (or an
appropriately converted equivalent); ST deviation is the maximum net deviation
during exercise or recovery, in millimetres.
"""
import argparse
import csv
import json
import math
import sys


FIELDS = ("exercise_minutes", "st_deviation_mm", "angina_index")


def _normalised(data):
    return {str(key).strip().lower().replace("-", "_").replace(" ", "_"): value
            for key, value in data.items() if key is not None}


def _nonnegative_number(value, name):
    if isinstance(value, bool):
        raise ValueError(f"{name} must be a finite non-negative number")
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(f"{name} must be a finite non-negative number") from exc
    if not math.isfinite(number) or number < 0:
        raise ValueError(f"{name} must be a finite non-negative number")
    return number


def calculate_score(present):
    """Calculate DTS from exercise_minutes, st_deviation_mm and angina_index.

    Angina index: 0 = none; 1 = non-limiting; 2 = exercise-limiting.
    Risk strata: low >= +5, moderate -10 through < +5, high < -10.
    All required values must be supplied; no clinical value is imputed.
    """
    if not isinstance(present, dict):
        raise ValueError("input must be a dictionary")
    fields = _normalised(present)
    missing = [name for name in FIELDS if name not in fields]
    if missing:
        raise ValueError("missing required field(s): " + ", ".join(missing))

    minutes = _nonnegative_number(fields["exercise_minutes"], "exercise_minutes")
    st_mm = _nonnegative_number(fields["st_deviation_mm"], "st_deviation_mm")
    angina_raw = fields["angina_index"]
    if isinstance(angina_raw, bool) or str(angina_raw).strip() not in ("0", "1", "2"):
        raise ValueError("angina_index must be 0 (none), 1 (non-limiting), or 2 (limiting)")
    angina = int(str(angina_raw).strip())
    score = minutes - 5 * st_mm - 4 * angina
    tier = "low" if score >= 5 else "moderate" if score >= -10 else "high"
    return {
        "score": score,
        "tier": tier,
        "detail": {
            "exercise_minutes": minutes,
            "st_deviation_mm": st_mm,
            "angina_index": angina,
            "st_penalty": 5 * st_mm,
            "angina_penalty": 4 * angina,
        },
    }


def assess_row(row):
    """Assess one CSV row using the same validation as a single calculation."""
    return calculate_score(row)


def _safe_csv_cell(value):
    """Prevent spreadsheet formula execution from untrusted CSV passthrough data."""
    text = "" if value is None else str(value)
    if text.lstrip(" \t\r\n").startswith(("=", "+", "-", "@")) or text[:1] in ("\t", "\r", "\n"):
        return "'" + text
    return text


def process_csv(inp, out):
    """Read clinical inputs and write a scored CSV; validate before creating output."""
    if not isinstance(inp, str) or not inp.strip():
        raise ValueError("input path must be a non-empty string")
    if not isinstance(out, str) or not out.strip():
        raise ValueError("output path must be a non-empty string")
    with open(inp, "r", newline="", encoding="utf-8-sig") as source:
        reader = csv.DictReader(source)
        columns = reader.fieldnames
        if not columns:
            raise ValueError("CSV file must have a header")
        normalised = [_normalised({key: None}).popitem()[0] for key in columns]
        if len(normalised) != len(set(normalised)):
            raise ValueError("CSV has duplicate column names")
        rows = []
        for number, row in enumerate(reader, start=2):
            if None in row:
                raise ValueError(f"row {number}: too many columns")
            try:
                result = assess_row(row)
            except ValueError as exc:
                raise ValueError(f"row {number}: {exc}") from exc
            output = {key: _safe_csv_cell(value) for key, value in row.items()}
            output.update(score=result["score"], tier=result["tier"],
                          detail=json.dumps(result["detail"], separators=(",", ":")))
            rows.append(output)
    output_columns = list(columns) + [field for field in ("score", "tier", "detail") if field not in columns]
    with open(out, "w", newline="", encoding="utf-8") as target:
        writer = csv.DictWriter(target, fieldnames=output_columns)
        writer.writeheader()
        writer.writerows(rows)
    return rows


def build_parser():
    parser = argparse.ArgumentParser(
        description="Duke Treadmill Score (standard Bruce protocol exercise ECG)"
    )
    commands = parser.add_subparsers(dest="command", required=True)
    single = commands.add_parser("single", help="Score one exercise treadmill test")
    single.add_argument("--exercise-minutes", type=float, help="Bruce exercise duration, minutes")
    single.add_argument("--st-deviation-mm", type=float, help="Maximum net ST deviation, mm")
    single.add_argument("--angina-index", type=int, choices=(0, 1, 2), help="0 none, 1 non-limiting, 2 limiting")
    single.add_argument("--json", help="JSON object with the same three input fields")
    batch = commands.add_parser("batch", help="Score a CSV with the three required columns")
    batch.add_argument("--input", required=True)
    batch.add_argument("--output", required=True)
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "single":
            if args.json is not None:
                if any(getattr(args, field) is not None for field in FIELDS):
                    raise ValueError("use --json OR individual input options, not both")
                data = json.loads(args.json)
            else:
                data = {field: getattr(args, field) for field in FIELDS
                        if getattr(args, field) is not None}
            result = calculate_score(data)
            print(json.dumps(result, sort_keys=True))
            return 0
        rows = process_csv(args.input, args.output)
        print(f"Processed {len(rows)} row(s) -> {args.output}")
        return 0
    except (ValueError, TypeError, OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
