#!/usr/bin/env python3
"""
parse_mbox.py — Parse one or more Apple Mail / Thunderbird .mbox exports into a
normalized per-email dataset for writing-voice analysis.

Generic, no personal data baked in. Pass the owner's own email addresses so the
parser can tell self-addressed mail apart and (for Sent folders) confirm
authorship.

USAGE
  python3 parse_mbox.py \
      --mbox "/path/Sent.mbox/mbox:Sent" \
      --mbox "/path/Archive.mbox/mbox:Archive" \
      --owner you@example.com --owner you@work.com \
      --out /path/to/output_dir

Each --mbox is "FILEPATH:LABEL". For Apple Mail, the real file is the `mbox`
file *inside* the .mbox bundle directory (e.g. "Sent.mbox/mbox").

OUTPUT (in --out)
  email_dataset.json   one row per message (includes author_text)
  email_dataset.csv    same minus author_text (for quick slicing)

DESIGN NOTES / LESSONS BAKED IN
  - Always prints counts and writes files; the caller MUST verify files exist on
    disk and recount before trusting any number (see handoff doc).
  - Strips quoted reply chains and signature blocks down to authored text.
  - Heuristic audience features are emitted but kept separate from raw facts.
"""
import argparse, mailbox, email, re, json, csv, html, statistics, collections, os, sys
from email.utils import parsedate_to_datetime, getaddresses

QUOTE_MARKERS = [
    re.compile(r'^On .*wrote:\s*$'),
    re.compile(r'^-+\s*Original Message\s*-+', re.I),
    re.compile(r'^-+\s*Forwarded message\s*-+', re.I),
    re.compile(r'^From:\s', re.I),
    re.compile(r'^Sent:\s', re.I),
    re.compile(r'^\s*>'),
    re.compile(r'^_{5,}$'),
    re.compile(r'^Begin forwarded message:', re.I),
]
SIG = re.compile(r'^(Sent from my (iPhone|iPad)|Get Outlook for|--\s*$)', re.I)

def get_plain(msg):
    plain = htmltext = None
    if msg.is_multipart():
        for part in msg.walk():
            if str(part.get('Content-Disposition', '')).startswith('attachment'):
                continue
            ct = part.get_content_type()
            if ct == 'text/plain' and plain is None:
                try: plain = part.get_content()
                except Exception:
                    try: plain = part.get_payload(decode=True).decode(part.get_content_charset() or 'utf-8', 'replace')
                    except Exception: pass
            elif ct == 'text/html' and htmltext is None:
                try: htmltext = part.get_content()
                except Exception:
                    try: htmltext = part.get_payload(decode=True).decode(part.get_content_charset() or 'utf-8', 'replace')
                    except Exception: pass
    else:
        try: plain = msg.get_content()
        except Exception:
            try: plain = msg.get_payload(decode=True).decode(msg.get_content_charset() or 'utf-8', 'replace')
            except Exception: plain = str(msg.get_payload())
    if plain: return plain
    if htmltext: return strip_html(htmltext)
    return ""

def strip_html(t):
    t = re.sub(r'(?is)<(script|style).*?>.*?</\1>', ' ', t)
    t = re.sub(r'(?s)<br\s*/?>', '\n', t)
    t = re.sub(r'(?s)</(p|div|tr|li)>', '\n', t)
    t = re.sub(r'(?s)<[^>]+>', ' ', t)
    return re.sub(r'[ \t]+\n', '\n', html.unescape(t))

def author_text(body):
    if not body: return ""
    body = body.replace('\r\n', '\n').replace('\r', '\n')
    out = []
    for ln in body.split('\n'):
        if any(p.match(ln) for p in QUOTE_MARKERS): break
        if SIG.match(ln.strip()): break
        out.append(ln)
    return re.sub(r'\n{3,}', '\n\n', "\n".join(out).strip())

def era(y):
    if y is None: return ""
    if y <= 2016: return "<=2016"
    if y <= 2020: return "2017-2020"
    return "2021+"

def greeting_form(text):
    for ln in text.split('\n'):
        s = ln.strip()
        if not s: continue
        low = s.lower()
        if low.startswith(('salaam', 'salam', 'assalam')): return "salaam"
        if re.match(r'^(hi|hey|hello)\b', low): return "hi_hey"
        if re.match(r'^dear\b', low): return "dear"
        if re.match(r'^(all|team|folks|everyone|gentlemen|gents)\b', low): return "group_collective"
        if re.match(r'^[A-Z][a-zA-Z\.]+(\s+[A-Z][a-zA-Z\.]+)?\s*-\s*$', s): return "name_dash"
        if re.match(r'^[A-Z][a-zA-Z\.]+(\s+[A-Z][a-zA-Z\.]+)?\s*-\s+\S', s): return "name_dash"
        if re.match(r'.*\bet al\s*:', s, re.I): return "name_etal"
        if re.match(r'^[A-Z][a-zA-Z\.]+\s*:\s*$', s): return "name_colon"
        if re.match(r'^[A-Z][a-zA-Z\.]+\s*:\s+\S', s): return "name_colon"
        if re.match(r'^[A-Z][a-zA-Z\.]+\s*,\s*$', s): return "name_comma"
        if re.match(r'^[A-Z][a-zA-Z\.]+(\s+[A-Z][a-zA-Z\.]+)?\s*$', s) and len(s) <= 24: return "name_only"
        return "none"
    return "none"

def signoff_form(text):
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    tail = " ".join(lines[-4:]).lower() if lines else ""
    if re.search(r'\bcheers\b', tail): return "cheers"
    if re.search(r'\bthank(s| you)\b', tail): return "thanks"
    if re.search(r'\b(best regards|warm regards|kind regards|best|regards|sincerely)\b', tail): return "best_regards"
    return "name_or_none"

def sentences(text):
    t = re.sub(r'\s+', ' ', text.replace('\n', ' ')).strip()
    return [s for s in re.split(r'(?<=[.!?])\s+', t) if s.strip()] if t else []

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--mbox', action='append', required=True, help='FILEPATH:LABEL (repeatable)')
    ap.add_argument('--owner', action='append', default=[], help='owner email address (repeatable)')
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    owners = {o.lower() for o in a.owner}
    os.makedirs(a.out, exist_ok=True)

    rows = []
    for spec in a.mbox:
        path, _, label = spec.rpartition(':')
        if not path:  # no label given
            path, label = spec, os.path.basename(spec)
        if not os.path.exists(path):
            print(f"!! MBOX NOT FOUND: {path}", file=sys.stderr); continue
        mb = mailbox.mbox(path)
        for msg in mb:
            frm = getaddresses([str(msg.get('From', ''))])
            from_addr = (frm[0][1].lower() if frm and frm[0][1] else "")
            tos = getaddresses([str(msg.get('To', '')), str(msg.get('Cc', ''))])
            to_addrs = [ad.lower() for _, ad in tos if '@' in ad]
            dt = None
            try: dt = parsedate_to_datetime(msg.get('Date'))
            except Exception: pass
            subj = str(msg.get('Subject', '')).strip()
            at = author_text(get_plain(msg))
            slens = [len(s.split()) for s in sentences(at)]
            rows.append({
                "source": label,
                "date": dt.isoformat() if dt else "",
                "year": dt.year if dt else "",
                "era": era(dt.year if dt else None),
                "from_addr": from_addr,
                "to_primary": to_addrs[0] if to_addrs else "",
                "to_domain": to_addrs[0].split('@')[-1] if to_addrs else "",
                "n_recipients": len(to_addrs),
                "is_self": bool(to_addrs) and all(ad in owners for ad in to_addrs),
                "from_owner": (from_addr in owners) if owners else None,
                "subject": subj,
                "is_reply": bool(re.match(r'^\s*re:', subj, re.I)),
                "word_count": len(at.split()),
                "greeting": greeting_form(at) if at else "none",
                "signoff": signoff_form(at) if at else "name_or_none",
                "lowercase_open": (at[:1].islower() if at else False),
                "double_space": bool(re.search(r'\.  ', at)),
                "space_before_bang": " !" in at,
                "space_before_q": " ?" in at,
                "two_dot_ellipsis": bool(re.search(r'(?<!\.)\.\.(?!\.)', at)),
                "smiley": bool(re.search(r':-?\)|:-?\(|;-?\)', at)),
                "avg_sentence_len": round(statistics.mean(slens), 1) if slens else 0,
                "fragment_present": any(1 <= x <= 3 for x in slens),
                "numbered_list": bool(re.search(r'^\s*\d+[\.\)]\s', at, re.M)),
                "empty_body": len(at.split()) == 0,
                "author_text": at,
            })

    if not rows:
        print("NO ROWS PARSED — check --mbox paths.", file=sys.stderr); sys.exit(1)

    json.dump(rows, open(os.path.join(a.out, "email_dataset.json"), "w"), ensure_ascii=False)
    cols = [k for k in rows[0] if k != "author_text"]
    with open(os.path.join(a.out, "email_dataset.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction='ignore'); w.writeheader()
        for r in rows: w.writerow({k: r[k] for k in cols})

    ne = [r for r in rows if not r['empty_body']]
    ds = sorted(r['date'] for r in rows if r['date'])
    print("TOTAL:", len(rows))
    print("authored (non-empty):", len(ne))
    print("by source:", dict(collections.Counter(r['source'] for r in rows)))
    print("date range:", (ds[0][:10] if ds else "?"), "->", (ds[-1][:10] if ds else "?"))
    print("WROTE:", os.path.join(a.out, "email_dataset.json"), "and .csv")

if __name__ == "__main__":
    main()
