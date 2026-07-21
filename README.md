# Exotic Science Timeline

**Nine centuries of anomaly claims, measured for the first time.**

An interactive record of documented claims about anomalous energy, propulsion, gravity, and material effects — from a twelfth-century overbalanced wheel to twenty-first-century precision nulls. Every entry carries a graded evidence coordinate rather than a verdict, and the lines connecting claims to the adversarial examinations that followed them are the point of the whole exhibit.

Published by **Advanced Rediscovery**. Data and classification standard: [EQO](https://github.com/shredEngineer/eqo).

---

## What this shows

Each mark is a dated record. Its position is time, its lane is the class of effect claimed, its colour is the region of the evidence lattice it occupies — a documentation profile, deliberately chosen to carry no valuation. The arcs are **resolution arcs**: they connect a claim to the examination that later tested it.

Two figures fall out of the record and are worth stating plainly. The median interval between a claim and its first documented adversarial examination is **six years**. The self-runner lineage — devices claimed to run without input — is **unbroken from 1150 to the present**, which is a statement about people rather than about physics.

Nothing here asserts that any claimed effect is real, and nothing here asserts that any is fabricated. The record grades how well each claim is documented, on six ordered axes, and lets the reader see which claims share an evidential situation regardless of what they claimed.

## How it is built

```
EQO repository (pinned)        this repository
  corpus + dating layer   ──►  base/timeline.json  ┐
                               overlay/overlay.json ├──►  tools/build.py  ──►  dist/index.html
                               viewer/template.html ┘
```

**The base is pinned, never edited here.** `base/timeline.json` is a copy of the dating layer from a specific commit of the standard's repository; `base/PIN` records exactly which one. Updating the base is a deliberate act with its own commit, so the page can always state which corpus version it is showing.

**The overlay is separate on purpose.** `overlay/overlay.json` holds enrichment keyed by record identifier and is rewritten wholesale by the upstream research process. It attaches to records under an `enrichment` key and **never overwrites a base field** — the build refuses rather than letting an overlay silently win, and it refuses again if the overlay references a record the pinned base does not contain, because that means the pin moved and the overlay is stale.

Build locally:

```bash
python3 tools/build.py     # -> dist/index.html
```

The output is a single self-contained file: all data inlined, no runtime fetches, no external dependencies. It works offline and can be archived by saving one file.

## Licence

Content and data: **CC BY 4.0** (`LICENSE`). Code — the build tool and CI: **Apache-2.0** (`LICENSE-CODE`).

Attribute as: **Dr.-Ing. Paul Wilhelm / Advanced Rediscovery, *Exotic Science Timeline*, CC BY 4.0.** The underlying corpus carries its own attribution; see the standard's repository.

## Provenance, stated up front

The underlying corpus was compiled with the assistance of a large language model from publicly documented claims, and every record carries its own documentation and provenance grades plus a separate confidence field for the compiler's own recall. **Verify against primary sources before citing.** This is not a caveat bolted on at the end — the whole instrument exists to make exactly this kind of grading explicit, and it would be incoherent to exempt itself.
