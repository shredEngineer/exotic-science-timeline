#!/usr/bin/env python3
"""Update the vendored standard vocabulary from a local checkout of the EQO repo.

    python3 tools/sync-standard.py [path-to-eqo-checkout]

Copies vocabulary.json, rewrites standard/PIN with the source commit and checksum,
and prints the diff summary. Deliberate, reviewed, committed — never run in CI.
"""
import hashlib, json, pathlib, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT.parent / "eqo"


def main() -> int:
    vocab = SRC / "vocabulary.json"
    if not vocab.exists():
        print(f"no vocabulary.json at {SRC} — pass the eqo checkout path", file=sys.stderr)
        return 1
    data = json.loads(vocab.read_text())
    version = data.get("eqo_version", "?")
    try:
        commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=SRC, capture_output=True,
                                text=True, check=True).stdout.strip()
        dirty = subprocess.run(["git", "status", "--porcelain", "vocabulary.json"], cwd=SRC,
                               capture_output=True, text=True, check=True).stdout.strip()
    except Exception as e:
        print(f"cannot read the source commit: {e}", file=sys.stderr)
        return 1
    if dirty:
        print("refusing: the source vocabulary.json has uncommitted changes — pin only committed state",
              file=sys.stderr)
        return 1

    dest = ROOT / "standard" / "vocabulary.json"
    dest.write_text(vocab.read_text())
    digest = hashlib.sha256(dest.read_bytes()).hexdigest()
    (ROOT / "standard" / "PIN").write_text(
        f"version {version}\nsource github.com/shredEngineer/eqo\ncommit {commit}\nsha256 {digest}\n")
    print(f"pinned vocabulary {version} @ {commit[:12]} ({digest[:16]}…)")
    print("review the diff, then commit standard/vocabulary.json and standard/PIN together")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
