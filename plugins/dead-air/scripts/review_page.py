"""Build the dated review page for a post:
python3 review_page.py <post.json> <out_dir> <calls.json> [--title "Dead Air: Hannibal"] [--h1 "Dead Air · The Hannibal order"] [--name dead-air-hannibal]
Defaults: title "Dead Air <Mon D>", h1 "Dead Air · <weekday, Mon D>", file dead-air-<date>.html."""
import json, html, sys
from pathlib import Path
def _opt(flag):
    return sys.argv[sys.argv.index(flag) + 1] if flag in sys.argv else None
post = json.load(open(sys.argv[1])); out = Path(sys.argv[2]); calls = json.load(open(sys.argv[3]))
T_OVR, H1_OVR, NAME = _opt("--title"), _opt("--h1"), _opt("--name")
e = html.escape
date, fmt = post["date"], post["format"]
stem = f"schmimknews-{date}-{fmt}"
y, m, d = (int(x) for x in date.split("-"))
MON = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()[m-1]
nice = f"{MON} {d} {y}"
labels = {"bundle": ["Cover"] + [f"Story {i} of 3" for i in (1, 2, 3)] + ["Closer"],
          "weekly": ["Cover"] + [f"Story {i} of 3" for i in (1, 2, 3)] + ["Closer"],
          "single": ["Cover", "The story", "Closer"],
          "deep": (["Cover", "The families", "What happened", "Both sides", "Who ran it", "Closer"] if ((post.get("deep") or {}).get("family") or {}).get("open") else ["Cover", "What happened", "Both sides", "Who ran it"] + (["The families"] if (post.get("deep") or {}).get("family") else []) + ["Closer"])}[fmt]
slides = "".join(f'<figure class="slide"><img src="{stem}-{i+1:02d}.png" alt="{e(a)}" width="1080" height="1350" loading="lazy"><figcaption><span class="n">{i+1:02d} · {labels[i]}</span><span class="alt">{e(a)}</span></figcaption></figure>' for i, a in enumerate(post["alt"]))
rows = "".join(f'<tr><td class="num">{i+1:02d}</td><td><b>{e(s.get("title") or s["headline"])}</b><br><span class="mono">{s["record_id"]}</span></td><td>{e(s["dateline"])}</td><td class="mono">{e(s.get("count") or s["stat"])}</td><td>{s["confidence"]}</td></tr>' for i, s in enumerate(post["stories"]))
reel_story = (post.get("reel") or {}).get("story") or post["stories"][0]
calls_html = "".join(f"<li><b>{e(c[0])}</b> {e(c[1])}</li>" for c in calls["calls"])
facts = "".join(f"<span>{e(k)} <b>{e(v)}</b></span>" for k, v in calls["facts"])
page = f'''<title>Dead Air {MON} {d}</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Big+Shoulders+Display:wght@800;900&family=Work+Sans:wght@400;600&family=IBM+Plex+Mono:wght@400;600&display=swap">
<style>
/* Layout: one review column; slides in a sideways strip like the carousel; the Reel beside its cover; copy blocks below. Single dark theme = the feed's own look. */
:root{{--ground:#0b0b0c;--raised:#161618;--ink:#f4f2ec;--muted:#a9a7a0;--signal:#ffb000;--hair:#2a2a2e;
--display:"Big Shoulders Display",Impact,"Arial Narrow",sans-serif;--sans:"Work Sans",system-ui,sans-serif;--mono:"IBM Plex Mono",ui-monospace,Menlo,monospace;color-scheme:dark}}
body{{background:var(--ground);color:var(--ink);font:16px/1.5 var(--sans);margin:0}}
.wrap{{max-width:1120px;margin:0 auto;padding-block:32px 64px;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px));display:flex;flex-direction:column;gap:40px}}
.kicker{{display:flex;align-items:center;gap:10px;font:600 13px/1.2 var(--mono);letter-spacing:3px;text-transform:uppercase;color:var(--muted)}}
.kicker i{{width:12px;height:12px;background:var(--signal);display:block}} .kicker b{{color:var(--ink)}}
h1{{font:900 clamp(48px,9vw,96px)/.92 var(--display);text-transform:uppercase;margin:12px 0 0;text-wrap:balance}}
h2{{font:600 13px/1.2 var(--mono);letter-spacing:3px;text-transform:uppercase;color:var(--muted);margin:0 0 14px}}
.facts{{display:flex;flex-wrap:wrap;gap:8px 28px;font:14px/1.4 var(--mono);color:var(--muted)}} .facts b{{color:var(--ink);font-weight:600}}
.strip{{display:flex;gap:16px;overflow-x:auto;scroll-snap-type:x mandatory;padding-bottom:12px}}
.slide{{margin:0;flex:0 0 min(300px,78vw);scroll-snap-align:start;display:flex;flex-direction:column;gap:10px}}
.slide img{{width:100%;height:auto;display:block;border:1px solid var(--hair)}}
.slide figcaption{{display:flex;flex-direction:column;gap:4px;font-size:13px;color:var(--muted)}}
.slide .n{{font:600 12px var(--mono);letter-spacing:2px;text-transform:uppercase;color:var(--ink)}}
.note{{font:13px var(--mono);color:var(--muted);margin:6px 0 0;max-width:75ch}}
.reel{{display:flex;flex-wrap:wrap;gap:24px;align-items:flex-start}}
.reel video{{width:min(360px,100%);height:auto;aspect-ratio:4/5;background:#000;border:1px solid var(--hair)}}
.reel .side{{flex:1 1 280px;min-width:0;display:flex;flex-direction:column;gap:10px;font-size:14px;color:var(--muted)}}
.copy{{background:var(--raised);padding:20px 22px;display:flex;flex-direction:column;gap:14px;min-width:0}}
.copy pre{{margin:0;white-space:pre-wrap;font:15px/1.55 var(--sans);color:var(--ink);max-width:68ch}}
.copy .bar{{display:flex;justify-content:space-between;align-items:center;gap:12px}}
button{{font:600 13px var(--mono);letter-spacing:2px;text-transform:uppercase;background:var(--signal);color:var(--ground);border:0;padding:10px 16px;cursor:pointer}}
button:focus-visible{{outline:2px solid var(--ink);outline-offset:3px}}
.cols{{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,420px),1fr));gap:24px}}
.tbl{{overflow-x:auto}} table{{border-collapse:collapse;width:100%;min-width:680px;font-size:14px}}
td,th{{text-align:left;vertical-align:top;padding:12px 12px 12px 0;border-top:1px solid var(--hair)}}
th{{font:600 11px var(--mono);letter-spacing:2px;text-transform:uppercase;color:var(--muted)}}
td.num{{font:900 28px/1 var(--display);color:var(--signal)}} .mono{{font:12px var(--mono);color:var(--muted)}}
ul.calls{{margin:0;padding-left:18px;display:flex;flex-direction:column;gap:8px;max-width:75ch}} ul.calls b{{color:var(--signal);font-weight:600}}
</style>
<main class="wrap">
<header><div class="kicker"><i></i><b>Schmim Knews</b><span>Dead Air · Review</span></div><h1>Dead Air · {nice}</h1></header>
<div class="facts">{facts}</div>
<section><h2>Reel · deep dive on the lead story · {e(calls["reel_length"])}, no audio</h2><div class="reel">
<video src="{stem}-reel.mp4" poster="{stem}-reel-cover.png" controls muted playsinline></video>
<div class="side"><span><b style="color:var(--ink)">{e(reel_story["headline"])}</b></span>
<span>Hook, what happened, both sides, who ran it, closer. Each line appears on its own and holds long enough to read. The audio track is empty so you can lay in music.</span>
<span>Cover image for the Reel is its first slide.</span></div></div></section>
<section><h2>Carousel · {len(post["alt"])} slides, in posting order</h2><div class="strip">{slides}</div>
<p class="note">Scroll sideways. Long-press or right-click a slide to save it. Each caption is that slide's alt text.</p></section>
<section class="cols">
<div class="copy"><div class="bar"><h2 style="margin:0">Carousel caption</h2><button type="button" data-copy="cap">Copy</button></div><pre id="cap">{e(post["caption"])}</pre></div>
<div class="copy"><div class="bar"><h2 style="margin:0">Reel caption</h2><button type="button" data-copy="rcap">Copy</button></div><pre id="rcap">{e(post["reel_caption"])}</pre></div>
</section>
<section><h2>Stories in this post</h2><div class="tbl"><table><thead><tr><th></th><th>Story · Airtable record</th><th>Broke</th><th>Count</th><th>Status</th></tr></thead><tbody>{rows}</tbody></table></div></section>
<section><h2>Calls made on this post</h2><ul class="calls">{calls_html}</ul></section>
</main>
<script>
document.querySelectorAll('[data-copy]').forEach(b=>b.addEventListener('click',()=>{{
 const el=document.getElementById(b.dataset.copy);
 const done=()=>{{b.textContent='Copied';setTimeout(()=>b.textContent='Copy',1600)}};
 const sel=()=>{{const r=document.createRange();r.selectNodeContents(el);const s=getSelection();s.removeAllRanges();s.addRange(r);b.textContent='Selected';}};
 try{{navigator.clipboard.writeText(el.textContent).then(done,sel)}}catch(e){{sel()}}
}}));
</script>'''
import re as _re
if T_OVR: page = _re.sub(r"<title>[^<]*</title>", lambda m: f"<title>{T_OVR}</title>", page, count=1)
if H1_OVR: page = _re.sub(r"<h1>[^<]*</h1>", lambda m: f"<h1>{H1_OVR}</h1>", page, count=1)
out.mkdir(parents=True, exist_ok=True)
fn = out / f"{NAME or 'dead-air-' + date}.html"
fn.write_text(page)
print(fn)
