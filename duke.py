#!/usr/bin/env python3
"""
Duke Treadmill Score Calculator
Duke Treadmill Score from duration, ST deviation and angina for CAD prognosis.
Points-based score with tiered action thresholds. Stdlib only.
"""
import argparse, csv, sys

FACTORS = [
        ("Smoking",1),
        ("Hypertension",1),
        ("Diabetes",1),
        ("Prior stroke",2),
        ("Vascular disease",1)
]

THRESHOLDS = [(2,"low"),(4,"moderate"),(100,"high")]

def calculate_score(present):
    """present: dict factor->bool or row dict with 1/0."""
    if not isinstance(present, dict):
        raise ValueError("present must be a dictionary")
    score=0; detail={}
    for name,w in FACTORS:
        # accept 1/0, true/false, yes/no, present key in dict
        val = present.get(name, present.get(name.lower().replace(" ","_"), 0))
        is_pos = str(val).lower() in ("1","true","yes","y") or val==1 or val is True
        if is_pos:
            score+=w
            detail[name]=w
    # tier
    tier="low"
    for thr,label in THRESHOLDS:
        if score<=thr: tier=label; break
        tier=label
    return {"score": score, "tier": tier, "detail": detail}

def assess_row(row):
    # row is dict from csv
    # map csv columns to present
    if not isinstance(row, dict):
        raise ValueError("row must be a dictionary")
    present = {}
    for k,v in row.items():
        if k:
            present[k]=v
            present[k.lower()]=v
    return calculate_score(present)

def process_csv(inp,out):
    import csv
    if not inp or not isinstance(inp, str):
        raise ValueError("input path must be a non-empty string")
    if not out or not isinstance(out, str):
        raise ValueError("output path must be a non-empty string")
    try:
        with open(inp, newline="", encoding="utf-8-sig") as f:
            r=csv.DictReader(f); rows=list(r); fn=r.fieldnames
    except FileNotFoundError:
        raise FileNotFoundError(f"Input file not found: {inp}")
    except PermissionError:
        raise PermissionError(f"Permission denied reading: {inp}")
    if not fn:
        raise ValueError(f"CSV file has no headers: {inp}")
    results=[]
    for row in rows:
        res=assess_row(row)
        merged={**row, "score": res["score"], "tier": res["tier"], "detail": ";".join(res["detail"].keys())}
        results.append(merged)
    try:
        with open(out,"w",newline="",encoding="utf-8") as f:
            w=csv.DictWriter(f, fieldnames=list(fn)+["score","tier","detail"]); w.writeheader(); w.writerows(results)
    except PermissionError:
        raise PermissionError(f"Permission denied writing: {out}")
    return results

def build_parser():
    p=argparse.ArgumentParser(prog="duke", description="Duke Treadmill Score Calculator")
    sub=p.add_subparsers(dest="cmd", required=True)
    s=sub.add_parser("single"); s.add_argument("--age", type=float); s.add_argument("--sex"); 
    for name,_ in FACTORS:
        s.add_argument("--"+name.lower().replace(" ","_").replace(">","_gt_").replace("/","_"), default="0")
    s.add_argument("--json")
    b=sub.add_parser("batch"); b.add_argument("--input", required=True); b.add_argument("--output", required=True)
    return p

def main(argv=None):
    import json as _json
    p=build_parser(); a=p.parse_args(argv)
    if a.cmd=="single":
        try:
            if a.json:
                present=_json.loads(a.json)
            else:
                present={k: getattr(a,k) for k in vars(a) if k not in ("cmd","json")}
            res=calculate_score(present); print(res); return 0
        except _json.JSONDecodeError as e:
            print(f"Error: Invalid JSON input: {e}", file=sys.stderr); return 1
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr); return 1
    if a.cmd=="batch":
        try:
            res=process_csv(a.input, a.output); print(f"Processed {len(res)} -> {a.output}"); return 0
        except (FileNotFoundError, PermissionError, ValueError) as e:
            print(f"Error: {e}", file=sys.stderr); return 1
    p.print_help(); return 1

if __name__=="__main__":
    import sys; sys.exit(main())
