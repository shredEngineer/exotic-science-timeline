# Exotic Science Timeline

**Nine centuries of anomaly claims, graded on a single evidence scale.**

An interactive record of documented claims about anomalous energy, propulsion, gravity, and material effects — from a twelfth-century overbalanced wheel to twenty-first-century precision nulls. Every entry carries a graded evidence coordinate rather than a verdict, and the lines connecting claims to the adversarial examinations that followed them are the point of the whole exhibit.

Published by **Advanced Rediscovery**. Data and classification standard: [EQO](https://github.com/shredEngineer/eqo).

---

## What this shows

Each mark is a dated record. Its position is time, its lane is the class of effect claimed, its colour is the region of the evidence lattice it occupies — a documentation profile, deliberately chosen to carry no valuation. The arcs are **resolution arcs**: they connect a claim to the examination that later tested it.

Two things fall out of the record and are worth stating plainly. The median interval between a claim and its first documented adversarial examination is **six years**. And claims of devices that run without input **recur across the entire nine centuries** — from a twelfth-century mercury wheel to the present, in thirty-seven records with long silences between them — which is a statement about people rather than about physics.

Nothing here asserts that any claimed effect is real, and nothing here asserts that any is fabricated. The record grades how well each claim is documented, on six ordered axes, and lets the reader see which claims share an evidential situation regardless of what they claimed.

## What is here

| Path | What it is |
|------|-----------|
| `corpus/` | The record itself — 189 identifiers across four append-only releases, classified per [EQO](https://github.com/shredEngineer/eqo) |
| `derived/timeline.json` | Normalized dating layer over the corpus: events, resolution arcs, eras, statistics |
| `overlay/overlay.json` | Enrichment keyed by record identifier, written by the research process rather than by hand |
| `viewer/` | The page template and its self-hosted assets |
| `tools/` | `timeline-extract.py` regenerates the dating layer · `check-persons.py` is the publication gate · `build.py` assembles the page |

The **classification standard** is separate and lives in its own repository. This one owns the data and the publication; that one owns the vocabulary and the rules.

**The overlay is kept apart on purpose.** It attaches to records under an `enrichment` key and **never overwrites a corpus field** — the build refuses rather than letting an overlay silently win, and refuses again if it references a record the corpus does not contain. Without that separation a hand-edit and a generated write would fight over the same lines, and after the third merge nobody could say which statement came from whom.

Build locally:

```bash
python3 tools/timeline-extract.py   # corpus -> derived/timeline.json
python3 tools/check-persons.py      # publication gate
python3 tools/build.py              # -> dist/index.html
```

The output is a single self-contained file: all data inlined, no runtime fetches, no external dependencies. It works offline and can be archived by saving one file.

## Licence

Content and data: **CC BY 4.0** (`LICENSE`). Code — the build tool and CI: **Apache-2.0** (`LICENSE-CODE`).

Attribute as: **Dr.-Ing. Paul Wilhelm / Advanced Rediscovery, *Exotic Science Timeline*, CC BY 4.0.** The underlying corpus carries its own attribution; see the standard's repository.

## Provenance, stated up front

The underlying corpus was compiled with the assistance of a large language model from publicly documented claims, and every record carries its own documentation and provenance grades plus a separate confidence field for the compiler's own recall. **Verify against primary sources before citing.** This is not a caveat bolted on at the end — the whole instrument exists to make exactly this kind of grading explicit, and it would be incoherent to exempt itself.
