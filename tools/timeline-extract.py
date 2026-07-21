#!/usr/bin/env python3
"""EQO/1 timeline extractor — normalizes dates across all corpus releases and
emits derived/timeline.json (events, arcs, eras, stats). Re-run after any
corpus release; a viewer consumes the output.

Run from the repository root:  python3 tools/timeline-extract.py
"""
import json, re, statistics, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
CORPUS = ROOT / "corpus"
OUT = ROOT / "derived" / "timeline.json"
RENDERS = "EQO/1 — corpus releases A + B + C + D"

FILES = [CORPUS / n for n in ("instances-a.json", "instances-b.json",
                              "instances-c.json", "instances-d.json")]
CENT = re.compile(r'(\d{1,2})(?:st|nd|rd|th)\s+century')
YEAR = re.compile(r'(\d{4})')
DEC  = re.compile(r'(\d{4})s')

def parse_years(s):
    """-> (start, end, precision, ongoing)"""
    if not s or s.strip() in ("-",""): return (None,None,"none",False)
    ongoing = bool(re.search(r'(present|ff\.?|\u2013\s*$|-\s*$)', s.strip()))
    m = CENT.search(s)
    if m:
        c = int(m.group(1)); return ((c-1)*100+50, (c-1)*100+99, "century", ongoing)
    years = [int(y) for y in YEAR.findall(s)]
    if not years: return (None,None,"none",ongoing)
    start, end = min(years), max(years)
    prec = "circa" if "c." in s else ("decade" if DEC.search(s) and len(set(years))==1 else "year")
    if DEC.search(s): end = max(end, int(DEC.search(s).group(1))+9)
    if ongoing: end = 2026
    return (start, end if end!=start or ongoing else None, prec, ongoing)

events, arcs = [], []
for f in FILES:
    d = json.load(open(f))
    for r in d.get("instances", []):
        if r["id"] == "ex:bhaskara-note": continue  # pointer record
        st, en, prec, ong = parse_years(r.get("years",""))
        if st is None: continue
        # Carry the WHOLE record, then add the derived fields. Enumerating
        # fields here is how a consumer silently loses data every time the
        # corpus grows a column — the page must be able to show everything.
        et = r.get("effect_types") or []
        lanes = sorted({e.split("-")[1] for e in et}) or ["SON"]
        ev_rec = dict(r)
        ev_rec.update({
            "lane": lanes[0],            # primary class — the chart places by this
            "lanes": lanes,              # every class the record carries
            "t_start": st, "t_end": en, "t_precision": prec, "ongoing": ong,
            "epistemotype": r.get("epistemotype", "EP-0"),
            "record_kind": r.get("record_kind", "observation"),
            "confidence": r.get("compilation_confidence", "high"),
            "years_raw": r.get("years", ""),
        })
        events.append(ev_rec)
        for rel in r.get("relations",[]):
            arcs.append({"source":r["id"],"target":rel["ref"],"type":rel["type"]})
    for doc in d.get("doctrines", []):
        st,en,prec,ong = parse_years(doc.get("years",""))
        if st is None: continue
        rec = dict(doc)
        rec.update({"lane":"DOC","lanes":["DOC"],"t_start":st,"t_end":en,
            "t_precision":prec,"ongoing":ong,"epistemotype":"EP-0","record_kind":"doctrine",
            "confidence":doc.get("compilation_confidence","high"),"e_signature":"",
            "signatures":[],"note":doc.get("summary",""),"years_raw":doc.get("years","")})
        events.append(rec)
    for nar in d.get("narratives", []):
        st,en,prec,ong = parse_years(nar.get("emergence",""))
        if st is None: continue
        rec = dict(nar)
        rec.update({"lane":"NAR","lanes":["NAR"],"t_start":st,"t_end":en,
            "t_precision":prec,"ongoing":ong,"epistemotype":"EP-0","record_kind":"narrative",
            "confidence":nar.get("compilation_confidence","high"),"e_signature":"",
            "signatures":[],"note":"Kernel: "+nar.get("factual_kernel","")+" / Lore: "+nar.get("lore_layer",""),
            "principals":nar.get("principals",""),"years_raw":nar.get("emergence","")})
        events.append(rec)

emap = {e["id"]:e for e in events}
arcs = [a for a in arcs if a["source"] in emap and a["target"] in emap]
lags = [abs(emap[a["source"]]["t_start"] - emap[a["target"]]["t_start"]) for a in arcs if a["type"]=="contradicts"]
from collections import Counter
per_year = Counter(e["t_start"] for e in events if e["record_kind"] not in ("doctrine","narrative"))
slf = [e for e in events if "S-SLF" in e["signatures"]]
eras = [[1100,1800,"I","Mechanical era — wheels & descriptions"],[1800,1900,"II","First instrument era"],
        [1900,1945,"III","Field & radiation era"],[1945,1989,"IV","Postwar laboratory era"],
        [1989,2005,"V","Contested-laboratory era"],[2005,2026,"VI","Video & network era"]]
_starts = [e["t_start"] for e in events if e["t_start"] is not None]
_ends   = [(e["t_end"] or e["t_start"]) for e in events if e["t_start"] is not None]
stats = {"events":len(events),
    # the span the RECORDS cover, never the era buckets: the buckets are round
    # numbers chosen to group them and would overstate the left endpoint
    "data_span":[min(_starts),max(_ends)] if _starts else None,
    "context_events":sum(1 for e in events if e["record_kind"] in ("doctrine","narrative")),"observation_events":sum(1 for e in events if e["record_kind"] not in("doctrine","narrative")),
    "arcs":len(arcs),"contradiction_arcs":len(lags),
    "median_adversarial_lag_years":statistics.median(lags) if lags else None,
    "densest_year":per_year.most_common(1)[0] if per_year else None,
    "self_runner_lineage_span":[min(e["t_start"] for e in slf),max((e["t_end"] or e["t_start"]) for e in slf)] if slf else None,
    "per_era":{lbl:sum(1 for e in events if a<=e["t_start"]<b) for a,b,_,lbl in [(x[0],x[1],x[2],x[2]+" "+x[3]) for x in eras]}}
out = {"renders_corpus":RENDERS,"events":events,"arcs":arcs,"eras":eras,"stats":stats}
OUT.parent.mkdir(exist_ok=True)
json.dump(out, open(OUT,"w"), indent=1)
print(json.dumps(stats, indent=1))
