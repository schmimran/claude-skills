#!/usr/bin/env python3
"""
analyze_voice.py — Aggregate a parsed dataset (from parse_mbox.py or parse_olm.py)
into voice statistics. Pure computation; writes a results.txt and prints it.

USAGE
  python3 analyze_voice.py --data /path/email_dataset.json --out /path/results.txt
  # optional: --webmail gmail.com,yahoo.com,...  to define the "personal" bucket

The audience split here is HEURISTIC (domain-based). Treat internal-vs-external
as directional, not exact. State this caveat in any findings doc.
"""
import argparse, json, collections, statistics

DEFAULT_WEBMAIL = {'gmail.com','yahoo.com','icloud.com','outlook.com','hotmail.com',
                   'aol.com','me.com','comcast.net','verizon.net','live.com','msn.com'}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--data', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--webmail', default="")
    a = ap.parse_args()
    webmail = set(x.strip().lower() for x in a.webmail.split(',') if x.strip()) or DEFAULT_WEBMAIL

    rows = json.load(open(a.data))
    ne = [r for r in rows if not r['empty_body']]

    def aud(r):
        if r.get('is_self'): return 'self'
        d = (r.get('to_domain') or '').lower()
        if not d: return 'unknown'
        return 'personal' if d in webmail else 'business'

    def pct(sub, k):
        n = len(sub) or 1; return round(100*sum(1 for r in sub if r.get(k))/n)
    def dist(sub, k, top=6):
        c = collections.Counter(r.get(k) for r in sub); n = sum(c.values()) or 1
        return ", ".join(f"{a} {round(100*v/n)}%" for a, v in c.most_common(top))
    def med(sub, k):
        v = [r[k] for r in sub if isinstance(r.get(k), (int, float))]
        return round(statistics.median(v), 1) if v else 0

    L = []
    L.append("VOICE RESULTS — computed from " + a.data)
    L.append(f"total messages: {len(rows)} | authored: {len(ne)}")
    L.append(f"by source: {dict(collections.Counter(r['source'] for r in rows))}")
    ds = sorted(r['date'] for r in rows if r['date'])
    if ds: L.append(f"date range: {ds[0][:10]} -> {ds[-1][:10]}")
    L.append(f"audience (heuristic): {dict(collections.Counter(aud(r) for r in ne))}")

    L.append("\n== CORE (all authored) ==")
    L.append("greeting: " + dist(ne, 'greeting', 8))
    L.append("signoff: " + dist(ne, 'signoff', 6))
    L.append(f"median words: {med(ne,'word_count')} | median avg_sentence: {med(ne,'avg_sentence_len')}")
    for t in ['fragment_present','numbered_list','double_space','two_dot_ellipsis',
              'space_before_bang','space_before_q','lowercase_open','smiley','is_reply']:
        L.append(f"  {t}: {pct(ne,t)}%")

    L.append("\n== BY AUDIENCE (heuristic) ==")
    for t in ['personal', 'business', 'self']:
        sub = [r for r in ne if aud(r) == t]
        if not sub: continue
        L.append(f"[{t}] n={len(sub)}")
        L.append("   greeting: " + dist(sub, 'greeting', 5))
        L.append("   signoff: " + dist(sub, 'signoff', 4))
        L.append(f"   medwords={med(sub,'word_count')} lowercase_open={pct(sub,'lowercase_open')}% "
                 f"numbered={pct(sub,'numbered_list')}% frag={pct(sub,'fragment_present')}% reply={pct(sub,'is_reply')}%")

    L.append("\n== BY ERA ==")
    for e in sorted({r['era'] for r in ne if r['era']}):
        sub = [r for r in ne if r['era'] == e]
        L.append(f"[{e}] n={len(sub)} medwords={med(sub,'word_count')} "
                 f"no_greeting={round(100*sum(1 for r in sub if r['greeting']=='none')/(len(sub) or 1))}% "
                 f"frag={pct(sub,'fragment_present')}% dbl_space={pct(sub,'double_space')}%")

    L.append("\n== TOP RECIPIENT DOMAINS (non-self) ==")
    c = collections.Counter(r['to_domain'] for r in ne if not r.get('is_self') and r.get('to_domain'))
    for dom, n in c.most_common(20): L.append(f"  {n:5} {dom}")

    open(a.out, 'w').write("\n".join(L))
    print("\n".join(L))
    print("\nWROTE:", a.out)

if __name__ == "__main__":
    main()
