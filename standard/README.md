# Pinned standard vocabulary

`vocabulary.json` is a vendored copy of the [EQO](https://github.com/shredEngineer/eqo)
standard's machine-readable vocabulary export — every registry and enumeration in one
validated file. The build and the checks read this copy, never the specification prose
and never the network: the page must build offline and deterministically.

`PIN` records the adoption: the standard version, the exact commit the copy was taken
from, and its SHA-256. CI verifies on every push that the vendored file still matches
the pinned checksum — a silently edited copy fails the build.

To move to a newer standard release, run `python3 tools/sync-standard.py` with the
standard's repository checked out beside this one, review the diff, and commit copy and
PIN together. Updating the pin is a deliberate act, not a side effect.
