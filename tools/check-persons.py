#!/usr/bin/env python3
"""Publication gate: no unsourced allegation about a named person.

A record whose subject is the honest grading of documentation cannot itself
assert, without a source, that a named individual committed a crime.

    python3 tools/check-persons.py     # exit 0 clean, 1 on findings

A finding discharges by citing a primary source, by reporting the absence of a
finding, or by attributing the outcome to secondary sources while stating that it
has not been verified.
"""
import json, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
CORPUS = ROOT / "corpus"
OVERLAY = ROOT / "overlay" / "overlay.json"

ALLEGATION = re.compile(
    r'\b(fraud|fraudulent|convicted|conviction|criminal|indicted|swindl\w*|'
    r'charlatan|scam|embezzl\w*|con\s+man|deliberate deception|faked (?:the|his|her)|'
    r'sentenced|prosecuted)\b', re.I)
NO_PERSON = re.compile(r"^\s*$|magazine|report|community|anonymous|unknown|various|group|\(.*\)\s*$", re.I)
EXCULPATORY = re.compile(r'\bwithout a? (?:fraud )?finding|no (?:fraud )?finding|acquitt\w*|cleared\b', re.I)
ATTRIBUTED = re.compile(r'not verified against a primary source', re.I)


def main() -> int:
    records = []
    for f in sorted(CORPUS.glob("instances-*.json")):
        d = json.loads(f.read_text())
        for key in ("instances", "doctrines", "narratives"):
            for r in d.get(key, []):
                records.append((f.name, r))

    findings = []
    for fname, e in records:
        principals = (e.get("principals") or "").strip()
        if NO_PERSON.match(principals):
            continue
        text = " ".join(str(e.get(k, "")) for k in ("note", "summary", "lore_layer", "factual_kernel"))
        hits = sorted(set(m.lower() for m in ALLEGATION.findall(text)))
        if not hits:
            continue
        if e.get("refs"):
            continue  # sourced — a reader can check the claim
        if EXCULPATORY.search(text) or ATTRIBUTED.search(text):
            continue
        findings.append((e["id"], principals, hits, text.strip()[:150]))

    # The enrichment overlay publishes alongside the corpus and is checked to the
    # same standard: an allegation-shaped statement about a named principal must
    # carry a readable source or discharge itself in the text.
    by_id = {r["id"]: r for _, r in records}
    if OVERLAY.exists():
        overlay = json.loads(OVERLAY.read_text()).get("entries", {})
        for rid, entry in overlay.items():
            text = str(entry.get("text", ""))
            hits = sorted(set(m.lower() for m in ALLEGATION.findall(text)))
            if not hits:
                continue
            base = by_id.get(rid, {})
            principals = (base.get("principals") or "").strip()
            if NO_PERSON.match(principals):
                continue
            if str(entry.get("source", "")).startswith("https://"):
                continue  # sourced — a reader can check the claim
            if EXCULPATORY.search(text) or ATTRIBUTED.search(text):
                continue
            findings.append((f"overlay:{rid}", principals, hits, text.strip()[:150]))

    if not findings:
        print(f"check-persons: clean over {len(records)} records + overlay")
        return 0

    print(f"check-persons: {len(findings)} finding(s)\n", file=sys.stderr)
    for rid, who, hits, snippet in findings:
        print(f"  {rid}\n    principal : {who}\n    triggers  : {', '.join(hits)}"
              f"\n    text      : {snippet}…\n", file=sys.stderr)
    print("cite a primary source, report the absence of a finding, or attribute without asserting", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
