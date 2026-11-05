#!/usr/bin/env python3
"""SPEC §13 acceptance tests 1-7a and addendum v2.1 §F tests for the dead-air scripts, against the bundled fixtures.

  python3 check_fixtures.py --python <python with playwright> --fonts <@fontsource dir> --out <scratch dir>

Stdlib only. Runs render.py and review_page.py as subprocesses on temp copies of the fixtures,
so the fixtures themselves are never modified. Exits 1 if any test fails.
"""
import argparse, copy, hashlib, json, re, shutil, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent / "scripts"
FX = HERE / "fixtures"
DESIGN = FX / "design-system"
BUNDLE = json.loads((FX / "2026-10-31-bundle.json").read_text())
DEEP = json.loads((FX / "2026-10-31-deep-hannibal.json").read_text())
UPDATE = json.loads((FX / "2026-11-05-update.json").read_text())
sys.path.insert(0, str(SCRIPTS))
import render as render_mod   # stdlib-only at import time; playwright loads inside main()
import review_page as review_mod   # main() is guarded; importing it only defines helpers

ap = argparse.ArgumentParser()
ap.add_argument("--python", default=sys.executable)
ap.add_argument("--fonts", required=True)
ap.add_argument("--out", required=True)
A = ap.parse_args()
OUT = Path(A.out)
MARK = OUT / ".dead-air-test-out"
if OUT.exists() and any(OUT.iterdir()) and not MARK.exists():
    sys.exit(f"refusing to wipe {OUT}: not empty and not a previous test output dir")
shutil.rmtree(OUT, ignore_errors=True); OUT.mkdir(parents=True); MARK.touch()

results = []

def record(name, ok, detail=""):
    results.append((name, ok, detail))
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  ({detail})" if detail else ""))

def render(name, post, *extra):
    """Write the post to OUT/<name>.json, render into OUT/<name>/, return (exit code, stdout+stderr, out dir)."""
    p = OUT / f"{name}.json"; p.write_text(json.dumps(post, ensure_ascii=False, indent=1))
    d = OUT / name
    r = subprocess.run([A.python, str(SCRIPTS / "render.py"), str(p), str(DESIGN), str(d), "--fonts", A.fonts, *extra],
                       capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr, d

def reel_stats(log):
    m = re.search(r"reel: (\d+) steps, ([\d.]+) s", log)
    return (int(m.group(1)), float(m.group(2))) if m else (None, None)

def probe(mp4):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(mp4)],
                       capture_output=True, text=True)
    return float(r.stdout.strip() or 0)

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def length_matches(mp4, secs, tol=0.15):
    """The delivered MP4 runs as long as render.py says (one 30 fps frame of slack, plus rounding)."""
    return mp4.exists() and secs is not None and abs(probe(mp4) - secs) <= tol

def final_frame(d, slide_no):
    """The fully revealed frame of Reel slide n (its last reveal step)."""
    return sorted((d / ".reel-frames").glob(f"r{slide_no:02d}-*.png"))[-1]

def expect_fail(name, post, needle):
    code, log, _ = render(name, post)
    ok = code == 1 and needle in log
    record(name, ok, "" if ok else f"exit {code}; wanted '{needle}'")

# ---------- 1. both fixtures render clean ----------
def full_render_checks(name, post, pngs, steps, lo, hi, stem):
    code, log, d = render(name, post)
    n_png = len(list(d.glob(f"{stem}-[0-9][0-9].png")))
    st, secs = reel_stats(log)
    mp4, cover = d / f"{stem}-reel.mp4", d / f"{stem}-reel-cover.png"
    problems = json.loads((d / "checks.json").read_text())["problems"] if (d / "checks.json").exists() else ["no checks.json"]
    ok = code == 0 and not problems and n_png == pngs and st == steps and secs is not None and lo <= secs <= hi \
         and mp4.exists() and cover.exists() and length_matches(mp4, secs)
    record(name, ok, f"exit {code}, {n_png} PNGs, {st} steps, {secs} s reported, {probe(mp4) if mp4.exists() else '-'} s in the MP4, problems={problems}")
    return d

d_b = full_render_checks("1-bundle", BUNDLE, 5, 25, 43, 45, "schmimknews-2026-10-31-bundle")
d_h = full_render_checks("1-hannibal", DEEP, 6, 28, 56, 58, "schmimknews-2026-10-31-deep")
stem_h = "schmimknews-2026-10-31-deep"
record("1-hannibal Reel opens on the families slide",
       sha(final_frame(d_h, 1)) == sha(d_h / f"{stem_h}-02.png"), "Reel slide 1 == carousel slide 2 (families)")
record("1-hannibal cover is the Flash hook",
       sha(d_h / f"{stem_h}-reel-cover.png") == sha(d_h / f"{stem_h}-01.png"), "reel-cover == carousel slide 1")

# ---------- 2-5. copy checks ----------
p = copy.deepcopy(BUNDLE); p["stories"][0]["stat"] = "9 of the 10 we could check: nothing."
expect_fail("2-insider stat", p, "old insider phrasing")

p = copy.deepcopy(BUNDLE); p["stories"][0]["grid"][0] = "unchecked"   # NYT, not named in `us`
expect_fail("3-unchecked not named", p, "NYT is unchecked but not named in `us`")

p = copy.deepcopy(BUNDLE); p["caption"] = p["caption"].replace("Save this.", "The receipts. Save this.", 1)
expect_fail("4-receipts in caption", p, "banned phrase")

for key in ("caption", "reel_caption"):
    p = copy.deepcopy(BUNDLE); p[key] = p[key].split("\n\nSources\n")[0]
    expect_fail(f"4a-{key} Sources block removed", p, f"{key} must end with")
    p = copy.deepcopy(BUNDLE); p[key] = p[key].replace("Quwa;", "Quwa (2026);")
    expect_fail(f"4a-{key} Sources line no longer matches", p, f"{key} must end with")

p = copy.deepcopy(BUNDLE); del p["reel"]
expect_fail("5-bundle without reel", p, "every post needs `reel`")

# ---------- mode: adhoc (SPEC §7.4.1) ----------
def with_ran(post, mode):
    p = copy.deepcopy(post); s = p["stories"][0]
    s["grid"][1] = "ran"; s["stat"] = "Six major US outlets didn't run it."
    if mode is None: p.pop("mode", None)
    else: p["mode"] = mode
    return p

code, log, _ = render("adhoc-deep ran allowed", with_ran(DEEP, "adhoc"), "--only", "carousel")
record("adhoc-deep ran allowed", code == 0, "" if code == 0 else log.strip()[-300:])
expect_fail("adhoc-dashboard deep ran rejected", with_ran(DEEP, "dashboard"), "can't have a 'ran' square")
expect_fail("adhoc-deep without mode rejected", with_ran(DEEP, None), "can't have a 'ran' square")
p = copy.deepcopy(BUNDLE); p["mode"] = "adhoc"; p["stories"][1]["grid"][0] = "ran"
expect_fail("adhoc-bundle ran still rejected", p, "can't have a 'ran' square")
p = copy.deepcopy(DEEP); p["mode"] = "freeform"
expect_fail("adhoc-unknown mode rejected", p, "mode must be dashboard or adhoc")

# ---------- 6. a single from story 1 ----------
def single(flash, stat=None):
    p = copy.deepcopy(BUNDLE); s = p["stories"][0]
    if stat: s["stat"] = stat
    p.update(format="single", flash=flash, stories=[s], alt=[
        "Cover: Pakistan's army ordered drones from a firm tied to Trump's sons. Reuters ran it; nine other major US outlets didn't.",
        "The story: Pakistan's army signed a drone deal with Powerus, a US maker backed by a fund of Trump's sons.",
        "How we check: abroad counts at three or more major foreign outlets; at home it counts as missing when none of the 11 major US outlets ran it."])
    p.pop("bundle_hook")
    return p

# Story 1's copy was written for a bundle row and a Flash Reel cover. On a non-Flash single its headline
# runs 4 lines at hook-l (max 3) and its stat 3 lines (max 2): the render check must catch that.
code, log, d = render("6-single uncut copy overflows", single(False), "--only", "carousel")
probs = json.loads((d / "checks.json").read_text())["problems"] if (d / "checks.json").exists() else []
record("6-single uncut copy overflows", code == 1 and any("hook--l runs 4 lines" in x for x in probs), f"exit {code}, {probs}")

# The §0 fix is cutting copy, never shrinking type: a Flash cover (hook-m, 4 lines; allowed on singles, §8.3)
# and the §8.5 breaker sentence.
code, log, d = render("6-single", single(True, "Reuters ran it. Nine other major US outlets didn't."))
st, secs = reel_stats(log)
n = len(list(d.glob("schmimknews-2026-10-31-single-[0-9][0-9].png")))
record("6-single", code == 0 and n == 3 and (d / "schmimknews-2026-10-31-single-reel.mp4").exists(),
       f"exit {code}, {n} PNGs, Reel {st} steps / {secs} s" + ("" if code == 0 else f" {log.strip()[-300:]}"))

# ---------- 7. review page ----------
def review(post_json, d, calls, *flags):
    r = subprocess.run([sys.executable, str(SCRIPTS / "review_page.py"), str(post_json), str(d / "review"), str(calls), *flags],
                       capture_output=True, text=True)
    return r.returncode, list((d / "review").glob("*.html")), r.stdout + r.stderr

for tag, d, pj, calls in (("bundle", d_b, FX / "2026-10-31-bundle.json", FX / "2026-10-31-calls.json"),
                          ("hannibal", d_h, FX / "2026-10-31-deep-hannibal.json", FX / "2026-10-31-deep-hannibal-calls.json")):
    code, pages, log = review(pj, d, calls)
    media = sorted(f.name for f in d.iterdir() if f.suffix in (".png", ".mp4"))
    html_ = pages[0].read_text() if len(pages) == 1 else ""
    missing = [m for m in media if m not in html_]
    record(f"7-{tag} review page", code == 0 and len(pages) == 1 and not missing,
           f"{len(pages)} HTML file(s), {len(media)} media, missing={missing}" + (f" {log}" if code else ""))
    shutil.rmtree(d / "review")
code, pages, log = review(FX / "2026-10-31-deep-hannibal.json", d_h, FX / "2026-10-31-deep-hannibal-calls.json",
                          "--title", "Dead Air: Hannibal", "--h1", "Dead Air · The Hannibal order", "--name", "dead-air-hannibal")
html_ = pages[0].read_text() if pages else ""
record("7-review page --title --h1 --name",
       code == 0 and [x.name for x in pages] == ["dead-air-hannibal.html"]
       and "<title>Dead Air: Hannibal</title>" in html_ and "<h1>Dead Air · The Hannibal order</h1>" in html_,
       f"files={[x.name for x in pages]}")

# ---------- 7a. families slide closing instead of opening ----------
p = copy.deepcopy(DEEP); p["deep"]["family"]["open"] = False
code, log, d = render("7a-family-close", p)
st, secs = reel_stats(log)
ok = (code == 0
      and sha(d / f"{stem_h}-05.png") == sha(d_h / f"{stem_h}-02.png")   # carousel slide 5 is the families slide
      and sha(final_frame(d, 5)) == sha(d / f"{stem_h}-05.png")          # and so is Reel slide 5
      and sha(final_frame(d, 1)) == sha(d / f"{stem_h}-01.png")          # the Reel now opens on the hook
      and secs is not None and 50.5 <= secs <= 53.5
      and length_matches(d / f"{stem_h}-reel.mp4", secs))
record("7a-families at position 5, Reel ~52 s", ok,
       f"exit {code}, {st} steps, {secs} s reported, {probe(d / f'{stem_h}-reel.mp4') if code == 0 else '-'} s in the MP4")

# ---------- §7.4.3-4 flags ----------
code, log, d = render("flags --only reel --budget", BUNDLE, "--only", "reel", "--budget", "hook=6")
st, secs = reel_stats(log)
pngs = list(d.glob("*-[0-9][0-9].png"))
record("flags --only reel --budget hook=6", code == 0 and not pngs and st == 25 and secs is not None and secs > 44.5
       and (d / "schmimknews-2026-10-31-bundle-reel.mp4").exists(), f"exit {code}, {len(pngs)} carousel PNGs, {secs} s (default 43.9)")
for name, extra, needle in (("flags --budget unknown slide", ("--budget", "intro=3"), "unknown slide"),
                            ("flags --open-family not a number", ("--open-family", "long"), "not a number"),
                            ("flags --only bad value", ("--only", "gif"), "--only must be")):
    code, log, _ = render(name, BUNDLE, *extra)
    record(name, code != 0 and needle in log, "" if needle in log else log.strip()[-200:])

# ---------- code-review fixes ----------
# A re-render into the same folder leaves no stale slides: 6 slides, then 5 (families dropped).
p = copy.deepcopy(DEEP); del p["deep"]["family"]; p["alt"] = p["alt"][:1] + p["alt"][2:]
code1, _, d = render("stale-slides", DEEP, "--only", "carousel")
code2, log, _ = render("stale-slides", p, "--only", "carousel")
left = sorted(x.name for x in d.glob(f"{stem_h}-[0-9][0-9].png"))
record("stale slides cleared on re-render", code1 == 0 and code2 == 0 and len(left) == 5, f"{left}" + ("" if code2 == 0 else log[-200:]))

# Carousel-only run: calls without reel_length -> no Reel panel, no KeyError.
def calls_without_reel(name):
    p = OUT / name; cj = json.loads((FX / "2026-10-31-calls.json").read_text()); cj.pop("reel_length")
    p.write_text(json.dumps(cj)); return p

calls_c = calls_without_reel("carousel-only-calls.json")
code, pages, log = review(FX / "2026-10-31-bundle.json", d_b, calls_c)
html_ = pages[0].read_text() if pages else ""
record("carousel-only review page (no reel_length)", code == 0 and "bundle-05.png" in html_ and ".mp4" not in html_
       and 'id="rcap"' not in html_, log.strip()[-300:])
shutil.rmtree(d_b / "review", ignore_errors=True)

# A flag followed by another flag is a missing value, not a value.
r = subprocess.run([A.python, str(SCRIPTS / "render.py"), str(FX / "2026-10-31-bundle.json"), str(DESIGN), str(OUT / "flag-missing"),
                    "--only", "--fonts", A.fonts], capture_output=True, text=True)
record("flag with missing value refused", r.returncode != 0 and "--only needs a value" in r.stdout + r.stderr, (r.stdout + r.stderr).strip()[-200:])

# ================= addendum v2.1 §F =================
UPD_CALLS = FX / "2026-11-05-update-calls.json"
stem_u = "schmimknews-2026-11-05-update-gas-transit"

record("review_page.stem_of matches render.post_stem",
       all(review_mod.stem_of(p) == render_mod.post_stem(p) for p in (BUNDLE, DEEP, UPDATE)))

# ---------- F.3 count line (§E) ----------
none_story = {"grid": ["silent"] * 11, "stat": "None of the 11 biggest US newsrooms ran it."}
e1 = render_mod.stat_errors(none_story)
e2 = render_mod.stat_errors(dict(none_story, grid=["silent"] * 9 + ["unchecked"] * 2, stat="9 of the 10 we could check: nothing."))
e3 = render_mod.stat_errors(dict(none_story, grid=["silent"] * 9 + ["unchecked"] * 2, stat="9 of the 10 outlets didn't run it."))
record("F3 'None of the 11 biggest US newsrooms ran it.' passes", e1 == [], f"{e1}")
record("F3 '9 of the 10 we could check: nothing.' fails", any("insider phrasing" in x for x in e2), f"{e2}")
record("F3 '9 of the 10' alone still fails", any("insider phrasing" in x for x in e3), f"{e3}")

# ---------- F.1 update companion: 4 slides + ~20 s Reel ----------
code, log, d_u = render("F1-update", UPDATE)
st, secs = reel_stats(log)
n_png = len(list(d_u.glob(f"{stem_u}-[0-9][0-9].png")))
problems = json.loads((d_u / "checks.json").read_text())["problems"] if (d_u / "checks.json").exists() else ["no checks.json"]
mp4 = d_u / f"{stem_u}-reel.mp4"
record("F1 update renders 4 slides and a 5-step ~17 s Reel",
       code == 0 and not problems and n_png == 4 and st == 5 and secs is not None and 16.5 <= secs <= 17.5
       and length_matches(mp4, secs), f"exit {code}, {n_png} PNGs, {st} steps, {secs} s, problems={problems}")
if code == 0:
    record("F1 update Reel opens on the Then slide (carousel slide 2)", sha(final_frame(d_u, 1)) == sha(d_u / f"{stem_u}-02.png"))
    record("F1 update Reel ends on the Closer (carousel slide 4)", sha(final_frame(d_u, 5)) == sha(d_u / f"{stem_u}-04.png"))
    record("F1 update Reel cover is the UpdateCover", sha(d_u / f"{stem_u}-reel-cover.png") == sha(d_u / f"{stem_u}-01.png"))
    for k in range(2, 4):   # each pickup lights its square on its own step
        record(f"F1 update Reel step {k} differs from step {k+1}", sha(final_frame(d_u, k)) != sha(final_frame(d_u, k + 1)))

# The day's post and its companion on one review page: a Nov 5 day post (the bundle fixture, re-dated, a different ask).
day = copy.deepcopy(BUNDLE); day["date"] = "2026-11-05"
code_d, log_d, d_day = render("F1-day", day, "--only", "carousel")
calls_day = calls_without_reel("F1-day-calls.json")
code, pages, log = review(OUT / "F1-day.json", d_day, calls_day, "--companion", str(FX / "2026-11-05-update.json"), str(UPD_CALLS))
html_ = pages[0].read_text() if pages else ""
media = sorted(f.name for f in d_day.iterdir() if f.suffix == ".png") + sorted(f.name for f in d_u.iterdir() if f.suffix in (".png", ".mp4"))
missing = [m for m in media if m not in html_]
record("F1 day's post + Update companion on one review page",
       code_d == 0 and code == 0 and len(pages) == 1 and not missing and 'id="cap-1"' in html_ and 'id="rcap-1"' in html_,
       f"{len(pages)} page(s), missing={missing} " + (log or log_d).strip()[-200:])
shutil.rmtree(d_day / "review", ignore_errors=True)
same_ask = copy.deepcopy(UPDATE); same_ask["ask"] = day["ask"]
sa = OUT / "F1-same-ask.json"; sa.write_text(json.dumps(same_ask, ensure_ascii=False))
code, _, log = review(OUT / "F1-day.json", d_day, calls_day, "--companion", str(sa), str(UPD_CALLS))
record("F1 companion with the day's ask refused", code != 0 and "day's ask" in log, log.strip()[-200:])
shutil.rmtree(d_day / "review", ignore_errors=True)

# ---------- F.4 update copy checks ----------
p = copy.deepcopy(UPDATE); del p["update"]["topic_line"]
expect_fail("F4 missing topic_line", p, "update.topic_line is missing")
p = copy.deepcopy(UPDATE); p["update"]["pickups"] = p["update"]["pickups"][:1]
expect_fail("F4 'ran' square without a dated pickup", p, "Reuters is 'ran' in the grid but has no dated pickup")
p = copy.deepcopy(UPDATE); p["update"]["pickups"][1]["date"] = ""
expect_fail("F4 pickup without a date", p, "must read 'Mon D'")
p = copy.deepcopy(UPDATE); p["stories"][0]["headline"] = "Update: WSJ ran it 14 days late."
expect_fail("F4 wrong 'N days late'", p, "headline says 14 days late; WSJ ran it 15 days")
p = copy.deepcopy(UPDATE); p["update"]["then_grid"][2] = "ran"
expect_fail("F4 then_grid with a 'ran' square", p, "then_grid can't have a 'ran' square")
p = copy.deepcopy(UPDATE); p["update"]["still_dark"] = "Nine of the 11 still haven't, as of Nov 2."
expect_fail("F4 still_dark count off the grid", p, "still_dark says 9; the grid has 8 silent")
p = copy.deepcopy(UPDATE); p["update"]["posted"] = "2026-11-01"
expect_fail("F4 pickup on or before our post is a correction", p, "that's a correction to report, not an Update")
p = copy.deepcopy(UPDATE); p["flash"] = True
expect_fail("F4 Flash Update cover", p, "never Flash")
code, log, d_t = render("F4-long topic_line", dict(copy.deepcopy(UPDATE), update=dict(UPDATE["update"],
    topic_line="Trump's envoys pitched Kyiv on reopening Russian gas transit through Ukraine to Europe, and urged European capitals to buy far more of it.")), "--only", "carousel")
probs = json.loads((d_t / "checks.json").read_text())["problems"] if (d_t / "checks.json").exists() else []
record("F4 topic_line over 2 lines fails", code == 1 and any("p.lede runs" in x and "max 2" in x for x in probs), f"exit {code}, {probs}")

# ---------- F.1 / F.2 / F.5 the day's plan (plan_day.py) ----------
def plan(inp):
    p = OUT / "plan-in.json"; p.write_text(json.dumps(inp))
    r = subprocess.run([sys.executable, str(SCRIPTS / "plan_day.py"), str(p)], capture_output=True, text=True)
    return json.loads(r.stdout) if r.returncode == 0 else {"error": r.stderr}

def story(sid, status="Flagged", **kw):
    return dict({"id": sid, "status": status, "confirmation": "Verified", "days_dark": 10, "silent": 10}, **kw)

def row(rid, post_date, fmt, stories, status="Ready", slot=None):
    return {"id": rid, "post_date": post_date, "format": fmt, "status": status, "stories": stories,
            "carousel_slot": slot or f"{post_date}T10:00:00-04:00"}

NOV5 = {"run_date": "2026-11-05", "now": "2026-11-05T06:00:00-05:00"}
base_rows = [row("rowOct22", "2026-10-22", "bundle", ["gas", "s2", "s3"]), row("rowOct31", "2026-10-31", "bundle", ["s4", "s5", "s6"])]
base_stories = [story("gas", "Covered", first_pickup={"outlet": "WSJ", "date": "2026-11-01"}),
                story("oil", override=True), story("s7"), story("s8")]
pl = plan(dict(NOV5, ig_posts=base_rows, stories=base_stories))
ok = pl.get("day", {}).get("format") == "single" and pl["day"]["eligible"][:1] == ["oil"] \
     and [c["story"] for c in pl["companions"]] == ["gas"] and not pl["corrections"]
record("F1 plan: one Covered story -> the day's normal single + one Update companion (two IG rows)", ok, json.dumps(pl)[:300])

pl = plan(dict(NOV5, ig_posts=base_rows + [row("rowOct10", "2026-10-10", "single", ["intel"])],
               stories=base_stories + [story("intel", "Covered", first_pickup={"outlet": "CNN", "date": "2026-10-10"})]))
corr = [c for c in pl.get("corrections", []) if c["story"] == "intel"]
record("F2 measurement miss -> no Update, a 'Correction due' line",
       "intel" not in [c["story"] for c in pl.get("companions", [])] and len(corr) == 1
       and corr[0]["line"].startswith("Correction due: intel, posted 2026-10-10, said CNN hadn't run it; CNN ran it 2026-10-10."),
       json.dumps(pl.get("corrections"))[:300])

rows5 = [row("rowNov2", "2026-11-02", "single", ["s7"], slot="2026-11-02T08:00:00-05:00")]
pl = plan(dict(NOV5, ig_posts=rows5, stories=[story("s7"), story("s8")]))
sk = {s["id"]: s["reason"] for s in pl["day"]["skipped"]}
record("F5 Ready row with a past slot blocks a repeat within 7 days",
       sk.get("s7") == "posted in the last 7 days" and pl["assumed_posted"] == ["rowNov2"], json.dumps(pl["day"])[:300])
pl = plan(dict(NOV5, ig_posts=[row("rowNov5", "2026-11-05", "single", ["s7"], slot="2026-11-05T08:00:00-05:00")],
               stories=[story("s7"), story("s8")]))
record("F5 Ready row with a future slot is not yet posted", pl["assumed_posted"] == [] and "s7" in pl["day"]["eligible"], json.dumps(pl)[:300])
pl = plan(dict(NOV5, ig_posts=[row("rowOct20", "2026-10-20", "single", ["s9"])], stories=[story("s8")]))
record("D stale Ready rows (>7 days past slot) listed", [s["id"] for s in pl["stale_ready"]] == ["rowOct20"], json.dumps(pl["stale_ready"]))

three = [story(f"g{i}", "Covered", first_pickup={"outlet": "AP", "date": f"2026-11-0{i}"}) for i in (3, 1, 2)]
pl = plan(dict(NOV5, ig_posts=[row("rowOct25", "2026-10-25", "bundle", ["g1", "g2", "g3"])], stories=three + [story("s8")]))
record("A.3 three Updates: two companions oldest pickup first, one deferred",
       [c["story"] for c in pl["companions"]] == ["g1", "g2"] and [c["story"] for c in pl["deferred_updates"]] == ["g3"],
       json.dumps(pl)[:300])
# Yesterday's companion is the newest row: it is skipped for alternation (the last day's post was the Oct 31 bundle),
# and its story is never updated twice.
pl = plan(dict(NOV5, ig_posts=base_rows + [row("rowNov4u", "2026-11-04", "update", ["gas"], slot="2026-11-04T15:00:00-05:00")],
               stories=[s for s in base_stories if s["id"] != "oil"]))
record("A an earlier Update row is skipped for alternation and never repeats",
       pl["companions"] == [] and pl["day"]["format"] == "single" and "last post was a bundle" in pl["day"]["rule"],
       json.dumps(pl)[:300])

# ---------- code-review fixes (PR #59) ----------
def copy_errs(mut):
    p = copy.deepcopy(UPDATE); mut(p)
    try: return render_mod.check_copy(p)
    except Exception as e: return [f"CRASH {type(e).__name__}: {e}"]

for name, mut, needle in (
    ("non-ISO posted reported, not raised", lambda p: p["update"].__setitem__("posted", "Oct 22"), "update.posted 'Oct 22' must be YYYY-MM-DD"),
    ("empty stories reported, not raised", lambda p: p.__setitem__("stories", []), "update needs 1 stories, got 0"),
    ("then_story not an object reported", lambda p: p["update"].__setitem__("then_story", "x"), "then_story must be the story object"),
    ("then_story without days_dark reported", lambda p: p["update"]["then_story"].pop("days_dark"), "then_story.days_dark is missing"),
    ("pickups not objects reported", lambda p: p["update"].__setitem__("pickups", ["WSJ"]), "pickups must be a list of"),
    ("duplicate pickup outlet rejected", lambda p: p["update"]["pickups"].append(dict(p["update"]["pickups"][0])), "listed twice"),
    ("pickups out of date order rejected", lambda p: p["update"]["pickups"].reverse(), "must be oldest first"),
    ("future pickup date is a typo, not a correction", lambda p: p["update"]["pickups"][1].__setitem__("date", "Nov 15"), "is after the run date"),
    ("breaker_date overrides the dateline for N days late", lambda p: p["update"].__setitem__("breaker_date", "2026-10-18"),
     "headline says 15 days late; WSJ ran it 14 days"),
):
    e = copy_errs(mut)
    record(f"review-fix {name}", any(needle in x for x in e) and not any(x.startswith("CRASH") for x in e), f"{e}")
e = copy_errs(lambda p: (p["update"].__setitem__("breaker_date", "2026-10-18"),
                         p["stories"][0].__setitem__("headline", "Update: WSJ ran it 14 days late.")))
record("review-fix breaker_date: a headline counted from it passes", e == [], f"{e}")

# plan_day: the weekly may repeat this week's stories (Sunday Nov 8).
SUN = {"run_date": "2026-11-08", "now": "2026-11-08T06:00:00-05:00"}
wk_rows = [row("rowNov3", "2026-11-03", "single", ["w1"]), row("rowNov5", "2026-11-05", "bundle", ["w2", "w3", "w4"])]
pl = plan(dict(SUN, ig_posts=wk_rows, stories=[story(f"w{i}") for i in range(1, 5)]))
record("review-fix weekly may repeat this week's stories",
       pl["day"]["format"] == "weekly" and len(pl["day"]["eligible"]) == 4 and not pl["day"]["skipped"], json.dumps(pl["day"])[:300])
pl = plan(dict(NOV5, ig_posts=wk_rows[:1], stories=[story("w1"), story("w2")]))
record("review-fix non-weekly still skips this week's stories",
       {s["id"]: s["reason"] for s in pl["day"]["skipped"]} == {"w1": "posted in the last 7 days"}, json.dumps(pl["day"])[:300])

# plan_day: Airtable's UTC 'Z' timestamps parse; a slot without an offset is a clean error.
pl = plan(dict(NOV5, ig_posts=[row("rowNov2z", "2026-11-02", "single", ["s7"], slot="2026-11-02T13:00:00.000Z")], stories=[story("s7"), story("s8")]))
record("review-fix Airtable 'Z' slot parses and counts as posted", pl.get("assumed_posted") == ["rowNov2z"], json.dumps(pl)[:300])
pl = plan(dict(NOV5, ig_posts=[row("rowNaive", "2026-11-02", "single", ["s7"], slot="2026-11-02T08:00")], stories=[story("s7")]))
record("review-fix slot without offset is a clean error", "has no UTC offset" in pl.get("error", ""), str(pl)[:300])

# plan_day: --format bundle that can't be met says the flag was overridden.
pl = plan(dict(NOV5, format_override="bundle", ig_posts=[], stories=[story("s7"), story("s8")]))
record("review-fix --format bundle fallback names the override",
       pl["day"]["format"] == "single" and pl["day"]["rule"].startswith("--format bundle overridden by rule 5"), pl["day"]["rule"])

# ---------- summary ----------
failed = [r for r in results if not r[1]]
print(f"\n{len(results) - len(failed)}/{len(results)} passed")
sys.exit(1 if failed else 0)
