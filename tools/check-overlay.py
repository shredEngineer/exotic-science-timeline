#!/usr/bin/env python3
"""Publication gate: the enrichment overlay carries only public provenance.

    python3 tools/check-overlay.py     # exit 0 clean, non-zero on findings

The overlay (overlay/overlay.json) is written wholesale by the publisher's
research process. Whatever that process knows internally, nothing may reach
this repository that is not already public. Three mechanical layers:

1.  Public provenance (load-bearing). Every entry's `source` resolves to
    something already public: a record id present in this corpus, or a URL on
    the allowlisted public-archive set — verified LIVE on every run. doi.org
    sources are verified against the DOI handle API (a handle exists or it
    does not; publisher bot-walls cannot fake a handle into existence), all
    other hosts by fetching the page and requiring HTTP 200. An unpublished
    document has no live public URL and structurally cannot pass.

2.  Token screen. Structural patterns no public overlay text has any business
    containing (private path fragments, internal registry ids), plus a hashed
    screen whose plaintext is maintained upstream — hashing keeps the screened
    vocabulary out of this repository while keeping the check enforceable here
    and in CI.

3.  Person statements are checked by tools/check-persons.py, whose scope
    includes this overlay.

The build (tools/build.py) separately refuses entries that shadow base-record
fields or reference unknown record ids.
"""
import hashlib
import json
import pathlib
import re
import sys
import time
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
OVERLAY = ROOT / "overlay" / "overlay.json"
CORPUS = ROOT / "corpus"

RELATIONS = {"patent", "literature", "analysis", "corpus"}
RECORD_ID = re.compile(r"^(ex|doc|nar):[a-z0-9][a-z0-9-]*$")

ALLOWED_HOSTS = {"patents.google.com", "arxiv.org", "doi.org"}
# The publisher's own research pages: host + path prefix, nothing wider.
ALLOWED_PREFIXES = ("https://advanced-rediscovery.com/research/",)

# Layer 2a — structural patterns (plain; shape-anchored generics only — an
# internal tracking id or a machine field name has no business in public prose).
STRUCTURAL = re.compile(r"\bIP-\d|derived_from", re.I)

# Layer 2b — hashed screen. Each entry is (token_length, sha256(token)) over
# lowercase alphanumeric-normalized text. The plaintext list is maintained
# upstream and never ships here; hashing keeps the screen enforceable in CI
# without publishing the vocabulary it screens for.
HASHED = [
    (5, "d42f124333b5259e933c8ddb8124c6e3e6e55cb0e0661254db3c8929d0bf9f87"),
    (5, "3ecdccae8323e7c0b7a429fe5c941b058c83efe90aea8f1e1a96c3fe84ec16c4"),
    (5, "2c30bb551b537408b39172ea79eb9692ac305fec0f90a46ad38e5e10a6dcad77"),
    (14, "e029946f0ec5f5c72c400a6d88cc5f77a91c3b2cd39f17b9493a2c4755a9e789"),
    (11, "f0784f4b2f45af5b89bc696b0f3b2a184a993ca68a3aa5c0f52b2d2711678a5c"),
    (9, "37d3fe002ea1eb52d44d1c8c5716c10be80766e51f8c88226548f52311ec07b3"),
    (7, "23ea3310ba5747785fbdd3927836096fea4e1f09814707b1ffafc8cc4cb1c0df"),
    (6, "6a4339e30b52c38eb477cf29115223bbb2b8d11ee1bcab8ffd77ad0ce40b8c19"),
    (8, "c2bfd1c2d82f13a736c7dd3cb4f8bbe10d033aa0a36cce974851aef8e54b3466"),
    (5, "e6f0a1fbb43c89196dcfcbef85908f19ab4c5f7cc4f4c452284697757683d7ef"),
    (10, "02e50afea67ea1f34246ff36cc2c2828e85d6be4adbbf20b947cd238526db1ce"),
    (12, "b6b4881207b5a52699eed4a07c1787bca797903b6c1a26cdeb9a08735196789e"),
    (5, "6ccce4863b70f258d691f59609d31b4502e1ba5199942d3bc5d35d17a4ce771d"),
]


def corpus_ids():
    ids = set()
    for f in sorted(CORPUS.glob("instances-*.json")):
        d = json.loads(f.read_text())
        for key in ("instances", "doctrines", "narratives"):
            for r in d.get(key, []):
                ids.add(r["id"])
    return ids


def fetch(url, timeout=25):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (overlay-gate)"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.status


def source_is_public(src, ids, errors):
    if RECORD_ID.match(src):
        if src not in ids:
            errors.append(f"corpus source {src!r} is not a record in this corpus")
            return
        return
    if not src.startswith("https://"):
        errors.append(f"source {src!r} is neither a record id nor an https URL")
        return
    host = src.split("/", 3)[2]
    if host == "doi.org":
        doi = src.split("doi.org/", 1)[1]
        probe = "https://doi.org/api/handles/" + doi
    elif host in ALLOWED_HOSTS:
        probe = src
    elif src.startswith(ALLOWED_PREFIXES):
        probe = src
    else:
        errors.append(f"source host {host!r} is not on the public-archive allowlist")
        return
    last = None
    for attempt in (1, 2):
        try:
            status = fetch(probe)
            if status == 200:
                return
            last = f"HTTP {status}"
        except Exception as exc:  # noqa: BLE001 — any failure is a red gate
            last = str(exc)
        time.sleep(2)
    errors.append(f"source {src!r} did not verify live ({last}) — probe {probe}")


def normalized(text):
    return re.sub(r"[^a-z0-9]", "", text.lower())


def hashed_hit(text):
    norm = normalized(text)
    for length, digest in HASHED:
        for i in range(0, max(0, len(norm) - length + 1)):
            if hashlib.sha256(norm[i:i + length].encode()).hexdigest() == digest:
                return True
    return False


def main() -> int:
    if not OVERLAY.exists():
        print("check-overlay: no overlay file — nothing to check")
        return 0
    raw = json.loads(OVERLAY.read_text())
    entries = raw.get("entries", {})
    if not entries:
        print("check-overlay: overlay empty — clean")
        return 0

    ids = corpus_ids()
    errors = []
    for rid, entry in entries.items():
        if not RECORD_ID.match(rid):
            errors.append(f"entry key {rid!r} is not a record id")
            continue
        if rid not in ids:
            errors.append(f"entry key {rid!r} does not exist in the corpus")
        if set(entry.keys()) != {"source", "relation", "text"}:
            errors.append(f"{rid}: entry keys must be exactly source/relation/text, got {sorted(entry)}")
            continue
        if entry["relation"] not in RELATIONS:
            errors.append(f"{rid}: relation {entry['relation']!r} not in {sorted(RELATIONS)}")
        text = entry["text"]
        if not isinstance(text, str) or not 20 <= len(text) <= 700:
            errors.append(f"{rid}: text must be 20-700 characters")
            continue
        blob = text + " " + str(entry["source"])
        if STRUCTURAL.search(blob):
            errors.append(f"{rid}: text or source matches a private-infrastructure pattern")
        if hashed_hit(blob):
            errors.append(f"{rid}: text or source matches the screened-vocabulary list")
        source_is_public(str(entry["source"]), ids, errors)

    if errors:
        print(f"check-overlay: {len(errors)} finding(s)\n", file=sys.stderr)
        for err in errors:
            print(f"  {err}", file=sys.stderr)
        return 1
    print(f"check-overlay: clean over {len(entries)} entries (all sources verified live)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
