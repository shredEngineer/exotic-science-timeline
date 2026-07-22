#!/usr/bin/env python3
"""Conformance gate: every corpus record agrees with the pinned standard vocabulary.

    python3 tools/check-coordinates.py     # exit 0 clean, 1 on findings

What it enforces, all against standard/vocabulary.json (never the spec prose):

  - the vendored vocabulary matches the checksum in standard/PIN
  - every phenomenon leaf, mechanism ref, context value, signature tag,
    epistemotype, record kind, relation type and confidence level is a
    vocabulary member (private X- extensions excepted where the standard
    allows them)
  - e_signature grammar, with each grade inside its axis range
  - the theory-embedding axis is exactly what the vocabulary's derivation_rules
    table derives from the mechanism edges (a record with no counting edge may
    carry the convention grade for orthodox anchors and null results)
  - the derived signatures and the exact epistemotype boundaries, both taken
    from derivation_rules rather than re-coded here
  - every relation resolves to a record in the corpus
  - a record graded D5 or better cites at least one reference

The derivation logic lives in the standard's vocabulary as data; this gate
interprets it. The one policy that is corpus-local, not standard: D5-and-up
requires a citation.
"""
import hashlib, json, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
CORPUS = ROOT / "corpus"
VOCAB = ROOT / "standard" / "vocabulary.json"
PIN = ROOT / "standard" / "PIN"


def main() -> int:
    bad = []

    pin = dict(line.split(None, 1) for line in PIN.read_text().splitlines() if line.strip())
    digest = hashlib.sha256(VOCAB.read_bytes()).hexdigest()
    if digest != pin.get("sha256"):
        print(f"standard/vocabulary.json does not match standard/PIN ({digest[:16]}… vs "
              f"{pin.get('sha256','?')[:16]}…) — run tools/sync-standard.py deliberately", file=sys.stderr)
        return 1

    v = json.loads(VOCAB.read_text())
    leaves = set(v["phenomena"]["leaves"])
    mechs = v["mechanisms"]
    facets = v["context_facets"]
    axes = v["axes"]
    eps = set(v["epistemotypes"])
    sigs = set(v["signatures"])
    roles = set(v["edge_roles"])
    rels = set(v["relation_types"])
    kinds = set(v["record_kinds"])
    conf = set(v["compilation_confidence"])
    rules = v["derivation_rules"]
    te = rules["theory_embedding"]
    sig_re = re.compile("^E1:" + "".join(f"{ax}([0-{axes[ax]['max']}]|x)" for ax in "DRCPTQ") + "$")

    def derive_t(mechanisms):
        """Interpret the theory-embedding table from the vocabulary."""
        grades = []
        for m in mechanisms:
            if m.get("role") in te["ignore_roles"]:
                continue
            status = mechs.get(m.get("ref"), {}).get("status")
            if status is None:
                continue
            for row in te["grade_by_edge"]:
                if row["status"] == status and row.get("role", m.get("role")) == m.get("role"):
                    grades.append(row["grade"])
                    break
        if not grades:
            return None  # no counting edge — no_edge_grade or the convention applies
        return max(grades)

    records, all_ids = [], set()
    for f in sorted(CORPUS.glob("instances-*.json")):
        d = json.loads(f.read_text())
        for key in ("instances", "doctrines", "narratives"):
            for r in d.get(key, []):
                all_ids.add(r["id"])
                if key == "instances":
                    records.append((f.name, r))
                elif r.get("compilation_confidence") not in conf:
                    bad.append(f"{r['id']}: compilation_confidence missing or unknown")

    for fname, r in records:
        rid = r["id"]
        for et in r.get("effect_types", []):
            if et not in leaves and not et.startswith("X-"):
                bad.append(f"{rid}: unknown phenomenon leaf {et}")
        for m in r.get("mechanisms", []):
            ref, role = m.get("ref"), m.get("role")
            if role not in roles:
                bad.append(f"{rid}: unknown edge role {role}")
            if ref not in mechs and not ref.startswith("X-"):
                bad.append(f"{rid}: unknown mechanism {ref}")
        t_derived = derive_t(r.get("mechanisms", []))
        for k, val in (r.get("context") or {}).items():
            if k not in facets:
                bad.append(f"{rid}: unknown context facet {k}")
                continue
            for x in (val if isinstance(val, list) else [val]):
                if x not in facets[k]["values"]:
                    bad.append(f"{rid}: unknown {facets[k]['registry_key']} value {x}")
        for sg in r.get("signatures", []) or []:
            if sg not in sigs:
                bad.append(f"{rid}: unknown signature {sg}")
        for rel in r.get("relations", []) or []:
            if rel.get("type") not in rels:
                bad.append(f"{rid}: unknown relation type {rel.get('type')}")
            if rel.get("ref") not in all_ids:
                bad.append(f"{rid}: relation to unknown record {rel.get('ref')}")
        for ret in r.get("retractions", []) or []:
            if not re.match(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$", ret.get("date", "")):
                bad.append(f"{rid}: retraction date is not ISO 8601: {ret.get('date')!r}")
            if not ret.get("ref", "").strip():
                bad.append(f"{rid}: retraction entry without a citation of the notice")
        if r.get("record_kind", "observation") not in kinds:
            bad.append(f"{rid}: unknown record_kind {r.get('record_kind')}")
        if "compilation_confidence" in r and r["compilation_confidence"] not in conf:
            bad.append(f"{rid}: unknown compilation_confidence {r['compilation_confidence']}")
        if r.get("epistemotype") is not None and r["epistemotype"] not in eps:
            bad.append(f"{rid}: unknown epistemotype {r['epistemotype']}")

        sig = r.get("e_signature", "")
        if not sig:
            continue
        m = sig_re.match(sig)
        if not m:
            bad.append(f"{rid}: e_signature fails the grammar: {sig}")
            continue
        grades = dict(zip("DRCPTQ", m.groups()))
        t = grades[te["axis"]]
        if t != "x":
            if t_derived is not None and int(t) != t_derived:
                bad.append(f"{rid}: {te['axis']}{t} but the edges derive {te['axis']}{t_derived}")
            if t_derived is None:
                allowed = {str(te["no_edge_grade"]), str(te["no_edge_convention"]["grade"])}
                if t not in allowed:
                    bad.append(f"{rid}: {te['axis']}{t} with no mechanism edge — only "
                               f"{te['axis']}{te['no_edge_grade']}, or the convention grade "
                               f"{te['axis']}{te['no_edge_convention']['grade']}, is derivable")
        n_x = sum(1 for g in grades.values() if g == "x")
        ep = r.get("epistemotype")
        for code, c in rules["epistemotype_constraints"].items():
            if ep != code:
                continue
            if "min_unknown_axes" in c and n_x < c["min_unknown_axes"]:
                bad.append(f"{rid}: {code} with only {n_x} axes at x — an assessed record is never unquantized")
            if "axis" in c and grades.get(c["axis"]) != str(c["equals"]):
                bad.append(f"{rid}: {code} requires {c['axis']}{c['equals']}, "
                           f"found {c['axis']}{grades.get(c['axis'])}")
        tagged = set(r.get("signatures", []) or [])
        for sg, c in rules["derived_signatures"].items():
            holds = grades.get(c["axis"]) == str(c["equals"])
            if holds and sg not in tagged:
                bad.append(f"{rid}: {c['axis']}{c['equals']} without the derived signature {sg}")
            if sg in tagged and not holds:
                bad.append(f"{rid}: {sg} but {c['axis']}{grades.get(c['axis'])}")
        d = grades["D"]
        if d != "x" and int(d) >= 5 and not r.get("refs"):
            bad.append(f"{rid}: graded D{d} but cites no reference")

    if bad:
        print(f"check-coordinates: {len(bad)} finding(s)", file=sys.stderr)
        for b in bad:
            print(f"  {b}", file=sys.stderr)
        return 1
    print(f"check-coordinates: clean over {len(records)} observation records "
          f"(vocabulary {v['eqo_version']} @ {pin['commit'][:12]})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
