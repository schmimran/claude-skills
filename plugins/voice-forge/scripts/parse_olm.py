#!/usr/bin/env python3
"""
parse_olm.py — Parse an Outlook for Mac .olm archive (Sent Items by default)
into the same normalized dataset schema as parse_mbox.py.

An .olm is a ZIP of per-message XML (Outlook OPF schema). This streams entries
from the zip; it never blanket-extracts the (often huge) archive and skips
attachments entirely.

USAGE
  python3 parse_olm.py \
      --olm "/path/Outlook for Mac Archive.olm" \
      --owner you@work.com --owner alias@work.com \
      --folder "Sent Items" \
      --out /path/to/output_dir

CRITICAL FIELD NOTE (this bit the original author):
  The email address attribute on <emailAddress> is OPFContactEmailAddressAddress
  (NOT OPFContactCopyEmailAddressAddress). Using the wrong name yields blank
  senders/recipients and silently corrupts the whole analysis. Verified below.

OUTPUT (in --out): olm_dataset.json, olm_dataset.csv  (same schema as mbox)
"""
import argparse, zipfile, re, json, csv, html, statistics, collections, os, sys
from xml.etree import ElementTree as ET
from datetime import datetime

CUT = [
    re.compile(r'^On .*wrote:\s*$'),
    re.compile(r'^-+\s*Original Message\s*-+', re.I),
    re.compile(r'^-+\s*Forwarded message\s*-+', re.I),
    re.compile(r'^From:\s', re.I), re.compile(r'^Sent:\s', re.I),
    re.compile(r'^To:\s', re.I), re.compile(r'^Subject:\s', re.I),
    re.compile(r'^\s*>'), re.compile(r'^_{5,}$'),
    re.compile(r'^Begin forwarded message:', re.I),
]
SIG = re.compile(r'^(Sent from my (iPhone|iPad)|Get Outlook for|Thanks,|Thank you,|Best,|Regards,)', re.I)
NS = re.compile(r'\{[^}]*\}')

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
        if any(p.match(ln) for p in CUT): break
        if SIG.match(ln.strip()): break
        out.append(ln)
    return re.sub(r'\n{3,}', '\n\n', "\n".join(out).strip())

def era(y):
    if y is None: return ""
    if y <= 2016: return "<=2016"
    if y <= 2018: return "2017-2018"
    if y <= 2020: return "2019-2020"
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

def textof(el): return (el.text or "").strip() if el is not None else ""

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--olm', required=True)
    ap.add_argument('--owner', action='append', default=[])
    ap.add_argument('--folder', default="Sent Items", help="message folder inside the archive")
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    owners = {o.lower() for o in a.owner}
    os.makedirs(a.out, exist_ok=True)

    if not zipfile.is_zipfile(a.olm):
        print("Not a zip/OLM:", a.olm, file=sys.stderr); sys.exit(1)
    z = zipfile.ZipFile(a.olm)
    prefix = f"Local/com.microsoft.__Messages/{a.folder}/"
    msgs = [n for n in z.namelist()
            if n.startswith(prefix) and n.split('/')[-1].startswith('message_') and n.endswith('.xml')]
    if not msgs:
        # help the caller discover the right folder name
        folders = sorted({n.split('/')[2] for n in z.namelist()
                          if n.startswith('Local/com.microsoft.__Messages/') and len(n.split('/')) > 3})
        print(f"No messages under {prefix!r}. Available folders: {folders}", file=sys.stderr)
        sys.exit(1)

    rows = []; errors = 0; skipped = 0
    for path in msgs:
        try: raw = z.read(path).decode('utf-8', 'replace')
        except Exception: errors += 1; continue
        try: root = ET.fromstring(raw)
        except ET.ParseError:
            try: root = ET.fromstring(raw.encode('utf-8', 'replace'))
            except Exception: errors += 1; continue
        em = root
        def find(t): return em.find('.//{*}' + t)
        sl = find('OPFMessageCopySenderList') or find('OPFMessageCopyFromAddresses')
        from_addr = ""
        if sl is not None:
            ad = sl.find('.//{*}emailAddress')
            if ad is not None:
                from_addr = (ad.get('OPFContactEmailAddressAddress', '') or "").lower()
        to_addrs = []
        for cont in ['OPFMessageCopyToAddresses', 'OPFMessageCopyCCAddresses']:
            node = find(cont)
            if node is not None:
                for ad in node.findall('.//{*}emailAddress'):
                    v = (ad.get('OPFContactEmailAddressAddress', '') or "").lower()
                    if '@' in v: to_addrs.append(v)
        if owners and from_addr and from_addr not in owners:
            skipped += 1; continue
        subj = textof(find('OPFMessageCopySubject'))
        st = textof(find('OPFMessageCopySentTime'))
        dt = None
        for fmt in ('%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M:%S%z'):
            try: dt = datetime.strptime(st, fmt); break
            except Exception: pass
        body = textof(find('OPFMessageCopyBody'))
        if not body or len(body) < 3:
            hb = find('OPFMessageCopyHTMLBody')
            if hb is not None and hb.text: body = strip_html(hb.text)
        elif '<' in body and ('</' in body or '<br' in body.lower() or '<p' in body.lower()):
            body = strip_html(body)
        at = author_text(body)
        slens = [len(s.split()) for s in sentences(at)]
        td = [v.split('@')[-1] for v in to_addrs]
        rows.append({
            "source": f"OLM:{a.folder}",
            "date": dt.isoformat() if dt else "",
            "year": dt.year if dt else "",
            "era": era(dt.year if dt else None),
            "from_addr": from_addr,
            "to_primary": to_addrs[0] if to_addrs else "",
            "to_domain": td[0] if td else "",
            "n_recipients": len(to_addrs),
            "is_self": bool(to_addrs) and all(v in owners for v in to_addrs),
            "from_owner": (from_addr in owners) if owners else None,
            "subject": subj,
            "is_reply": bool(re.match(r'^\s*re:', subj, re.I)),
            "is_forward": bool(re.match(r'^\s*fwd?:', subj, re.I)),
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
        print("NO ROWS PARSED — check --olm path, --owner addresses, and --folder name.", file=sys.stderr)
        sys.exit(1)

    json.dump(rows, open(os.path.join(a.out, "olm_dataset.json"), "w"), ensure_ascii=False)
    cols = [k for k in rows[0] if k != "author_text"]
    with open(os.path.join(a.out, "olm_dataset.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction='ignore'); w.writeheader()
        for r in rows: w.writerow({k: r[k] for k in cols})

    ne = [r for r in rows if not r['empty_body']]
    ds = sorted(r['date'] for r in rows if r['date'])
    print("PARSED rows:", len(rows), "| errors:", errors, "| skipped (not from owner):", skipped)
    print("authored non-empty:", len(ne))
    print("sender filled:", sum(1 for r in rows if r['from_addr']), "/", len(rows), "(should be ~all)")
    print("date range:", (ds[0][:10] if ds else "?"), "->", (ds[-1][:10] if ds else "?"))
    print("WROTE:", os.path.join(a.out, "olm_dataset.json"), "and .csv")

if __name__ == "__main__":
    main()
