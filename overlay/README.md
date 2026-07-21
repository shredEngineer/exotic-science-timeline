# Enrichment overlay

`overlay.json` is written wholesale by the upstream research process; it is not
hand-edited here.

Shape:

```json
{
  "overlay_version": 1,
  "generated": "YYYY-MM-DD",
  "entries": {
    "<record-id>": { "...": "..." }
  }
}
```

Each entry attaches to its record under an `enrichment` key. Two rules are
enforced by the build rather than by convention: an entry may never carry a key
that already exists on the base record, and every key in `entries` must resolve
to a record present in the pinned base. A violation of either fails the build —
the first because the base must stay authoritative, the second because it means
the pin moved and this file is stale.
