#!/usr/bin/env python3
"""
select_intentional.py — From a parsed dataset, select emails likely to show
deliberate/intentional word choice (de-escalation, pushback, bad news, feedback,
persuasion, gratitude, managing up), and shard them for careful reading.

The point is to surface candidates, NOT to draw conclusions. A human or a
reading-agent must read the shards and KEEP ONLY verbatim excerpts that exist in
the data (string-verify every quote — see verify_quotes.py and the handoff doc).

USAGE
  python3 select_intentional.py --data /path/dataset.json --out /path/dir \
      [--min-words 35] [--shards 3]
"""
import argparse, json, re, collections, math, os

CATS = {
 "ownership": r"\b(apolog|my (mistake|fault|bad)|fell short|dropped the ball|take (responsibility|ownership|accountab)|regret|on me|should have)\b",
 "empathy_deescalate": r"\b(understand your|appreciate your patience|i hear|i know (this|that|how)|recognize|i realize|frustrat|i get that|sensitive|difficult (position|spot)|tough)\b",
 "hedge_diplomacy": r"\b(i'?d (suggest|recommend|propose)|perhaps|might (be|make)|would it make sense|i wonder if|open to|candidly|to be (transparent|honest|clear)|want to be (clear|careful)|respectfully|gently)\b",
 "bad_news": r"\b(unfortunately|however|that said|i have to push back|i disagree|we (won'?t|can'?t|aren'?t able)|not able to|the (challenge|concern|issue) (is|here)|with respect)\b",
 "persuasion_framing": r"\b(the opportunity|i recommend|i propose|rationale|here'?s why|the risk|trade-?off|my (perspective|view|take)|i'?d argue|worth (considering|noting))\b",
 "gratitude_relational": r"\b(thank you for|i'?m grateful|i (really )?appreciate|i value|means a lot|grateful for)\b",
 "managing_up_politics": r"\b(align(ment)?|stakeholder|escalat|leadership|optics|navigate|buy-?in|socializ|get ahead of|positioning)\b",
 "people_feedback": r"\b(feedback|performance|growth|development|coaching|expectations|your role|career|raise the bar)\b",
}
COMP = {k: re.compile(v, re.I) for k, v in CATS.items()}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--data', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--min-words', type=int, default=35)
    ap.add_argument('--shards', type=int, default=3)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)

    rows = json.load(open(a.data))
    pool = []
    for idx, r in enumerate(rows):
        if r['empty_body'] or r['word_count'] < a.min_words: continue
        hits = [k for k, rx in COMP.items() if rx.search(r['author_text'])]
        if len(hits) >= 2:
            pool.append({"idx": idx, "date": r['date'][:10], "year": r['year'],
                         "to": r.get('to_primary', ''), "subject": r.get('subject', ''),
                         "categories": hits, "word_count": r['word_count'],
                         "text": r['author_text']})
    pool.sort(key=lambda x: (-len(x['categories']), -x['word_count']))

    cov = collections.Counter(c for p in pool for c in p['categories'])
    print("candidates (>=2 categories, >=%dw): %d" % (a.min_words, len(pool)))
    print("category coverage:", dict(cov.most_common()))

    json.dump(pool, open(os.path.join(a.out, "intentional_pool.json"), "w"), ensure_ascii=False, indent=1)
    per = math.ceil(len(pool) / max(1, a.shards))
    for s in range(a.shards):
        chunk = pool[s*per:(s+1)*per]
        if not chunk: break
        fn = os.path.join(a.out, f"intentional_shard_{s+1}.json")
        json.dump(chunk, open(fn, "w"), ensure_ascii=False, indent=1)
        print(f"  {os.path.basename(fn)}: {len(chunk)} emails")
    print("WROTE pool + shards to", a.out)

if __name__ == "__main__":
    main()
