#!/usr/bin/env python3
"""Dead Air · the project cache's VERSION doc (addendum v2.2 §A-B). Stdlib only.

  python3 -B cache_manifest.py <DA_ROOT> <out VERSION file> [--commit <sha>] [--date YYYY-MM-DD]

Lists every file the cache mirrors (scripts/, references/ and agents/ under DA_ROOT; never __pycache__ or
bytecode) with its sha256, after a three-line header. The file list is in `sha256sum -c` format, so a run
that has only the cache (and so none of this plugin's code yet) verifies it with coreutils alone:

  head -1 VERSION                                   ->  dead-air <version>
  sed '1,/^files$/d' VERSION | sha256sum -c --quiet   (run inside the downloaded cache folder)

Prints the paths it listed, one per line, so the command knows what to upload.
"""
import hashlib, json, sys
from datetime import date
from pathlib import Path

MIRRORED = ("scripts", "references", "agents")

def files(root):
    out = []
    for top in MIRRORED:
        for p in sorted((root / top).rglob("*")):
            if p.is_file() and "__pycache__" not in p.parts and p.suffix not in (".pyc", ".pyo"):
                out.append(p.relative_to(root).as_posix())
    return out

def manifest(root, commit="unknown", day=None):
    version = json.loads((root / ".claude-plugin/plugin.json").read_text())["version"]
    lines = [f"dead-air {version}", f"commit {commit}", f"date {day or date.today().isoformat()}", "files"]
    listed = files(root)
    lines += [f"{hashlib.sha256((root / f).read_bytes()).hexdigest()}  {f}" for f in listed]
    return "\n".join(lines) + "\n", listed

def _opt(flag):
    a = sys.argv
    if flag not in a: return None
    i = a.index(flag)
    if i + 1 >= len(a) or a[i + 1].startswith("--"): sys.exit(f"{flag} needs a value")
    return a[i + 1]

if __name__ == "__main__":
    if len(sys.argv) < 3 or sys.argv[1].startswith("--"): print(__doc__); sys.exit(2)
    root, out = Path(sys.argv[1]), Path(sys.argv[2])
    if not (root / ".claude-plugin/plugin.json").is_file(): sys.exit(f"{root} has no .claude-plugin/plugin.json")
    text, listed = manifest(root, _opt("--commit") or "unknown", _opt("--date"))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text)
    print("\n".join(listed))
