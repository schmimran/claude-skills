#!/usr/bin/env python3
"""
verify_quotes.py — Guard against fabricated examples. Confirms that each candidate
quote actually appears in the parsed dataset before it goes into any findings doc.

This is THE most important script in the bundle. In the original project, a
reading pass invented plausible-sounding quotes (and cited indexes that weren't
in the file). This catches exactly that.

USAGE
  python3 verify_quotes.py --data /path/dataset.json --quotes /path/quotes.json
  # quotes.json: [{"idx": 1234, "quote": "exact words..."}, ...]
  #   idx optional; if given, the quote must appear in THAT row.

Normalizes whitespace and unicode (curly quotes, non-breaking spaces) before
matching so trivial formatting differences don't cause false failures.
Exit code is non-zero if any quote fails — wire it into the workflow as a gate.
"""
import argparse, json, re, sys, unicodedata

def norm(s):
    s = unicodedata.normalize('NFKC', s or "")
    s = (s.replace('’', "'").replace('‘', "'")
           .replace('“', '"').replace('”', '"')
           .replace('–', '-').replace('—', '-')
           .replace('\xa0', ' '))
    return re.sub(r'\s+', ' ', s).strip().lower()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--data', required=True)
    ap.add_argument('--quotes', required=True)
    a = ap.parse_args()
    rows = json.load(open(a.data))
    corpus = [norm(r.get('author_text', '')) for r in rows]
    quotes = json.load(open(a.quotes))

    failures = 0
    for q in quotes:
        nq = norm(q['quote'])
        idx = q.get('idx')
        if idx is not None:
            ok = 0 <= idx < len(rows) and nq in corpus[idx]
            where = f"idx {idx}"
        else:
            ok = any(nq in c for c in corpus)
            where = "anywhere"
        if not ok: failures += 1
        print(("OK   " if ok else "FAIL ") + f"[{where}] {q['quote'][:70]!r}")

    print(f"\n{len(quotes)-failures}/{len(quotes)} verified.")
    if failures:
        print("!! FABRICATED OR MISLOCATED QUOTES PRESENT — do not ship.", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
