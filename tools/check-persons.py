#!/usr/bin/env python3
"""Publication gate over the pinned base: no unsourced allegation about a named person.

The upstream corpus enforces this on its own records. This is the same gate
re-asserted at the surface that actually publishes — a page must not inherit its
legal posture from a pin it cannot re-check.

    python3 tools/check-persons.py     # exit 0 clean, 1 on findings

A finding discharges by citing a primary source, by reporting the absence of a
finding, or by attributing the outcome to secondary sources while stating that it
has not been verified.
"""
import json, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
BASE = ROOT / "base" / "timeline.json"

ALLEGATION = re.compile(
    r'\b(fraud|fraudulent|convicted|conviction|criminal|indicted|swindl\w*|'
    r'charlatan|scam|embezzl\w*|con\s+man|deliberate deception|faked (?:the|his|her)|'
    r'sentenced|prosecuted)\b', re.I)
NO_PERSON = re.compile(r"^\s*$|magazine|report|community|anonymous|unknown|various|group|\(.*\)\s*$", re.I)
EXCULPATORY = re.compile(r'\bwithout a? (?:fraud )?finding|no (?:fraud )?finding|acquitt\w*|cleared\b', re.I)
ATTRIBUTED = re.compile(r'not verified against a primary source', re.I)


def main() -> int:
    if not BASE.exists():
        print(f"missing pinned base: {BASE}", file=sys.stderr)
        return 1

    events = json.loads(BASE.read_text()).get("events", [])
    findings = []
    for e in events:
        principals = (e.get("principals") or "").strip()
        if NO_PERSON.match(principals):
            continue
        text = str(e.get("note", ""))
        hits = sorted(set(m.lower() for m in ALLEGATION.findall(text)))
        if not hits:
            continue
        if EXCULPATORY.search(text) or ATTRIBUTED.search(text):
            continue
        findings.append((e["id"], principals, hits, text[:150]))

    if not findings:
        print(f"check-persons: clean over {len(events)} events in the pinned base")
        return 0

    print(f"check-persons: {len(findings)} finding(s) in the pinned base\n", file=sys.stderr)
    for rid, who, hits, snippet in findings:
        print(f"  {rid}\n    principal : {who}\n    triggers  : {', '.join(hits)}"
              f"\n    text      : {snippet}…\n", file=sys.stderr)
    print("fix upstream in the corpus, then re-pin base/timeline.json", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
