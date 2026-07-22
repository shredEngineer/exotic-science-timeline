#!/usr/bin/env python3
"""Build the published page from the pinned base corpus plus the enrichment overlay.

    python3 tools/build.py            # -> dist/index.html

Inputs
  base/timeline.json    the pinned dating layer from the EQO corpus (see base/PIN)
  overlay/overlay.json  enrichment keyed by record id; owned by the upstream
                        research process, rewritten wholesale on each run
  viewer/template.html  the viewer, with a __DATA__ placeholder

The merge is additive and non-destructive: overlay entries attach to their event
under an `enrichment` key. Base fields are never overwritten — an overlay that
tries is a bug, and the build says so rather than silently winning.
"""
import json, pathlib, shutil, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
BASE = ROOT / "derived" / "timeline.json"
OVERLAY = ROOT / "overlay" / "overlay.json"
VOCAB = ROOT / "standard" / "vocabulary.json"
TEMPLATE = ROOT / "viewer" / "template.html"
OUT = ROOT / "dist" / "index.html"

RESERVED = {"enrichment"}


def main() -> int:
    if not BASE.exists():
        print(f"missing dating layer: {BASE} — run tools/timeline-extract.py", file=sys.stderr)
        return 1

    data = json.loads(BASE.read_text())
    events = data.get("events", [])
    by_id = {e["id"]: e for e in events}

    overlay = {}
    if OVERLAY.exists():
        raw = json.loads(OVERLAY.read_text())
        overlay = raw.get("entries", {})

    attached, unknown, collisions = 0, [], []
    for rid, payload in overlay.items():
        target = by_id.get(rid)
        if target is None:
            unknown.append(rid)
            continue
        clashing = [k for k in payload if k in target and k not in RESERVED]
        if clashing:
            collisions.append((rid, clashing))
            continue
        target["enrichment"] = payload
        attached += 1

    if collisions:
        for rid, keys in collisions:
            print(f"overlay would overwrite base fields on {rid}: {keys}", file=sys.stderr)
        print("refusing to build — the overlay never overwrites the base", file=sys.stderr)
        return 2

    if unknown:
        print(f"overlay references {len(unknown)} unknown record id(s): "
              f"{', '.join(unknown[:5])}{' …' if len(unknown) > 5 else ''}", file=sys.stderr)
        print("refusing to build — a stale overlay means the base pin moved", file=sys.stderr)
        return 3

    data["enrichment_attached"] = attached

    # The page's labels, descriptions and definition anchors come from the
    # pinned standard vocabulary — the viewer hardcodes none of them, so a
    # vocabulary release updates the page by re-pinning, not by editing HTML.
    data["vocab"] = json.loads(VOCAB.read_text())

    # The data can change at any time, so the page states which commit it was
    # built from and when — a version a reader can actually go and look at.
    def git(*a):
        try:
            return subprocess.run(["git", *a], cwd=ROOT, capture_output=True,
                                  text=True, check=True).stdout.strip()
        except Exception:
            return ""
    data["data_commit"] = git("rev-parse", "HEAD")
    data["data_commit_date"] = git("log", "-1", "--format=%cs")

    # Span-derived framing facts are templated from the data, never hand-written,
    # so the prose and the meta tags can never drift from the corpus's actual span.
    span = data["stats"].get("data_span") or [None, None]
    start, end = span[0], span[1]
    WORDS = ["zero", "one", "two", "three", "four", "five", "six", "seven",
             "eight", "nine", "ten", "eleven", "twelve", "thirteen", "fourteen"]
    n = round((end - start) / 100) if (start and end) else 0
    centuries = WORDS[n].capitalize() if 0 <= n < len(WORDS) else str(n)

    html = (TEMPLATE.read_text()
            .replace("__DATA__", json.dumps(data, ensure_ascii=False))
            .replace("__SPAN_START__", str(start))
            .replace("__CENTURIES_CAP__", centuries))
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(html)

    # Static assets (favicon, brand fonts) ship alongside the page. Fonts are
    # self-hosted rather than pulled from a font CDN: a public page must not
    # hand its visitors' addresses to a third party.
    assets_src = ROOT / "viewer" / "assets"
    if assets_src.exists():
        dest = OUT.parent / "assets"
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(assets_src, dest)

    cname = ROOT / "CNAME"
    if cname.exists():
        (OUT.parent / "CNAME").write_text(cname.read_text())

    print(f"built {OUT.relative_to(ROOT)}  "
          f"events={len(events)}  enrichment_attached={attached}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
