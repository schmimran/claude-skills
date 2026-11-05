#!/usr/bin/env python3
"""SPEC §13 acceptance tests 1-7a, addendum v2.1 §F, addendum v2.2 §E (+ the 0.3.0 release tests) and the
0.4.0 bundle tests (the staged folder, every refusal, the review-page button, and a real-browser run of its downloads)
for the dead-air plugin, against the bundled fixtures.

  python3 -B check_fixtures.py --python <python with playwright> --fonts <@fontsource dir> --out <scratch dir>

Stdlib only. Runs render.py and review_page.py as subprocesses on temp copies of the fixtures,
so the fixtures themselves are never modified. Exits 1 if any test fails.
"""
import argparse, copy, hashlib, json, os, re, shutil, subprocess, sys, zipfile
from pathlib import Path

sys.dont_write_bytecode = True   # addendum v2.2 §I: importing the scripts below must not leave __pycache__/

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent / "scripts"
FX = HERE / "fixtures"
DESIGN = FX / "design-system"
# The Oct 31 bundle was posted before 0.3.0 with three stories: it renders only as a re-cut (addendum v2.2 §F).
BUNDLE3 = json.loads((FX / "2026-10-31-bundle.json").read_text())
BUNDLE = dict(BUNDLE3, recut_of="dead-air/posts/legacy/bundle-2026-10-31.json")
DEEP = json.loads((FX / "2026-10-31-deep-hannibal.json").read_text())
UPDATE = json.loads((FX / "2026-11-05-update.json").read_text())
sys.path.insert(0, str(SCRIPTS))
import render as render_mod   # stdlib-only at import time; playwright loads inside main()
import review_page as review_mod   # main() is guarded; importing it only defines helpers
import bundle_stage as bundle_mod  # same: main() is guarded

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
    r = subprocess.run([A.python, "-B", str(SCRIPTS / "render.py"), str(p), str(DESIGN), str(d), "--fonts", A.fonts, *extra],
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
    r = subprocess.run([sys.executable, "-B", str(SCRIPTS / "review_page.py"), str(post_json), str(d / "review"), str(calls), *flags],
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
r = subprocess.run([A.python, "-B", str(SCRIPTS / "render.py"), str(FX / "2026-10-31-bundle.json"), str(DESIGN), str(OUT / "flag-missing"),
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
    r = subprocess.run([sys.executable, "-B", str(SCRIPTS / "plan_day.py"), str(p)], capture_output=True, text=True)
    return json.loads(r.stdout) if r.returncode == 0 else {"error": r.stderr}

def story(sid, status="Flagged", **kw):
    return dict({"id": sid, "status": status, "confirmation": "Verified", "days_dark": 10, "silent": 10}, **kw)

def row(rid, post_date, fmt, stories, status="Ready", slot=None):
    return {"id": rid, "post_date": post_date, "format": fmt, "status": status, "stories": stories,
            "carousel_slot": slot or f"{post_date}T10:00:00-04:00"}

NOV5 = {"run_date": "2026-11-05", "now": "2026-11-05T06:00:00-05:00"}
base_rows = [row("rowOct22", "2026-10-22", "bundle", ["gas", "s2", "s3"]), row("rowOct31", "2026-10-31", "bundle", ["s4", "s5", "s6"])]
base_stories = [story("gas", "Covered", first_pickup={"outlet": "WSJ", "date": "2026-11-01"}),
                story("oil", override=True), story("s7"), story("s8"), story("s9")]
pl = plan(dict(NOV5, ig_posts=base_rows, stories=base_stories))
ok = pl.get("day", {}).get("format") == "bundle" and [x["id"] for x in pl["day"]["stories"]][:1] == ["oil"] \
     and len(pl["day"]["stories"]) == 4 and [c["story"] for c in pl["companions"]] == ["gas"] and not pl["corrections"]
record("F1 plan: one Covered story -> the day's four-story bundle (override leads) + one Update companion", ok, json.dumps(pl)[:300])

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
sk = {s["id"]: s["reason"] for s in pl["day"]["skipped"]}
record("J.1 a queued Ready row (future slot) counts as posted and holds its slot",
       pl["queued"] == ["rowNov5"] and pl["assumed_posted"] == [] and sk.get("s7") == "posted in the last 7 days"
       and pl["next_slot"] == "2026-11-06T08:00:00-05:00", json.dumps(pl)[:400])
pl = plan(dict(NOV5, ig_posts=[row("rowOct20", "2026-10-20", "single", ["s9"])], stories=[story("s8")]))
record("D stale Ready rows (>7 days past slot) listed", [s["id"] for s in pl["stale_ready"]] == ["rowOct20"], json.dumps(pl["stale_ready"]))

three = [story(f"g{i}", "Covered", first_pickup={"outlet": "AP", "date": f"2026-11-0{i}"}) for i in (3, 1, 2)]
pl = plan(dict(NOV5, ig_posts=[row("rowOct25", "2026-10-25", "bundle", ["g1", "g2", "g3"])], stories=three + [story("s8")]))
record("A.3 three Updates: two companions oldest pickup first, one deferred",
       [c["story"] for c in pl["companions"]] == ["g1", "g2"] and [c["story"] for c in pl["deferred_updates"]] == ["g3"],
       json.dumps(pl)[:300])
pl = plan(dict(NOV5, ig_posts=base_rows + [row("rowNov4u", "2026-11-04", "update", ["gas"], slot="2026-11-04T15:00:00-05:00")],
               stories=[x for x in base_stories if x["id"] != "oil"] + [story("s10")]))
record("A an earlier Update row's story is never updated again",
       pl["companions"] == [] and pl["day"]["format"] == "bundle", json.dumps(pl)[:300])

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

# plan_day: the weekly may repeat this week's stories (Sunday Nov 8), four of them.
SUN = {"run_date": "2026-11-08", "now": "2026-11-08T06:00:00-05:00"}
wk_rows = [row("rowNov3", "2026-11-03", "single", ["w1"]), row("rowNov5", "2026-11-05", "bundle", ["w2", "w3", "w4", "w5"])]
pl = plan(dict(SUN, ig_posts=wk_rows, stories=[story(f"w{i}") for i in range(1, 6)]))
record("review-fix weekly may repeat this week's stories",
       pl["day"]["format"] == "weekly" and len(pl["day"]["stories"]) == 4 and not pl["day"]["skipped"], json.dumps(pl["day"])[:300])
pl = plan(dict(NOV5, ig_posts=wk_rows[:1], stories=[story("w1"), story("w2")]))
record("review-fix non-weekly still skips this week's stories",
       {s["id"]: s["reason"] for s in pl["day"]["skipped"]} == {"w1": "posted in the last 7 days"}, json.dumps(pl["day"])[:300])

# plan_day: Airtable's UTC 'Z' timestamps parse; a slot without an offset is a clean error.
pl = plan(dict(NOV5, ig_posts=[row("rowNov2z", "2026-11-02", "single", ["s7"], slot="2026-11-02T13:00:00.000Z")], stories=[story("s7"), story("s8")]))
record("review-fix Airtable 'Z' slot parses and counts as posted", pl.get("assumed_posted") == ["rowNov2z"], json.dumps(pl)[:300])
pl = plan(dict(NOV5, ig_posts=[row("rowNaive", "2026-11-02", "single", ["s7"], slot="2026-11-02T08:00")], stories=[story("s7")]))
record("review-fix slot without offset is a clean error", "has no UTC offset" in pl.get("error", ""), str(pl)[:300])

# ================= addendum v2.2 §E + the 0.3.0 release tests =================
PLUGIN = HERE.parent
REPO = PLUGIN.parent.parent
COMMANDS = sorted((PLUGIN / "commands").glob("*.md"))

# ---------- the four-story bundle (§F) ----------
GAS = UPDATE["update"]["then_story"]   # the Oct 22 gas-transit story as we posted it: a real fourth story
STORY4 = dict(copy.deepcopy(GAS), grid=list(UPDATE["update"]["then_grid"]), title="Trump's envoys pitched Kyiv on reopening Russian gas transit",
              count="NYT ran it · 10 others didn't · 5 days", stat="The NYT ran it. Ten other major US outlets didn't.",
              meta="NYT Oct 17 · checked Oct 17–22")

def bundle4(hook="4 stories. Dead air.", fmt="bundle", still_dark=False, date=None):
    p = copy.deepcopy(BUNDLE3); s4 = copy.deepcopy(STORY4)
    if still_dark: s4.update(still_dark=True, count=f"Still dark: day {s4['days_dark']}.")
    p["stories"].append(s4); p.update(bundle_hook=hook, format=fmt)
    p["alt"] = [p["alt"][0].replace("3 US stories, 11 US outlets, dead air.", "4 stories, dead air.")] + \
               [a.replace(" of 3", " of 4") for a in p["alt"][1:4]] + \
               ["Story 4 of 4: Trump's envoys pitched Kyiv on reopening Russian gas transit. The NYT broke it; the other 10 major US outlets didn't run it."] + p["alt"][4:]
    if date: p["date"] = date
    return p

B4 = bundle4()
stem_b = "schmimknews-2026-10-31-bundle"
d_b4 = full_render_checks("v2.2 4-story bundle renders clean (hook: 4 stories. Dead air.)", B4, 6, 25, 43, 45, stem_b)
for hook, fmt in (("4 abroad. 0 here.", "bundle"), ("This week's dead air.", "weekly")):
    code, log, d = render(f"v2.2-4-story-{fmt}-{len(hook)}", bundle4(hook, fmt), "--only", "carousel")   # no quotes in folder names
    stem = f"schmimknews-2026-10-31-{fmt}"
    n = len(list(d.glob(f"{stem}-[0-9][0-9].png")))
    probs = json.loads((d / "checks.json").read_text())["problems"] if (d / "checks.json").exists() else ["no checks.json"]
    record(f"v2.2 4-story {fmt} renders clean with hook '{hook}'", code == 0 and n == 6 and not probs, f"exit {code}, {n} PNGs, {probs} {log.strip()[-200:] if code else ''}")
cover = render_mod.build_slides(B4)[0]
record("v2.2 the bundle hook is held to one line", 'data-maxlines="1">4 stories. Dead air.' in cover)
record("v2.2 story kickers read 'Dead Air · n of 4'", all(f"Dead Air · {i} of 4" in render_mod.build_slides(B4)[i] for i in range(1, 5)))

# a three-story bundle is refused (only a re-cut may carry three) — render.py and plan_day.py
expect_fail("v2.2 3-story bundle refused (no recut_of)", BUNDLE3, "bundle needs 4 stories, got 3")
p = copy.deepcopy(B4); p["bundle_hook"] = "3 US stories. 11 US outlets. Dead air."
expect_fail("v2.2 the old two-line hook refused on four stories", p, "bundle_hook must be one of")
p = copy.deepcopy(BUNDLE); p["bundle_hook"] = "4 stories. Dead air."
expect_fail("v2.2 a legacy re-cut keeps a legacy hook", p, "bundle_hook must be one of")
pl = plan(dict(NOV5, ig_posts=[], stories=[story("q1", override=True), story("q2"), story("q3")]))
record("v2.2 /dead-air plan with 3 qualifying stories: no carousel, the lead's Reel runs alone",
       pl["day"]["format"] is None and pl["day"]["reel_only"] == "q1" and len(pl["day"]["unfilled"]) == 1
       and pl["day"]["unfilled"][0].startswith("slot 4"), json.dumps(pl["day"])[:300])
pl = plan(dict(NOV5, format_override="single", ig_posts=[], stories=[story("q1")]))
record("v2.2 --format single refused by plan_day", "builds a bundle or a weekly" in pl.get("error", ""), str(pl)[:200])

# a Still-dark filler gets its kicker and its count line
SD = bundle4(still_dark=True)
code, log, d_sd = render("v2.2 Still-dark story", SD, "--only", "carousel")
sl = render_mod.build_slides(SD)
record("v2.2 Still-dark filler renders with its kicker and count line",
       code == 0 and "Dead Air · Still dark" in sl[4] and "Dead Air · 4 of 4" not in sl[4] and "Still dark: day 5." in sl[0],
       f"exit {code} {log.strip()[-200:] if code else ''}")
p = copy.deepcopy(SD); p["stories"][3]["count"] = "Still dark: day 9."
expect_fail("v2.2 Still-dark count line must match days dark", p, "Still-dark story count line must read 'Still dark: day 5.'")
p = copy.deepcopy(SD); p["stories"][2].update(still_dark=True, count=f"Still dark: day {p['stories'][2]['days_dark']}.")
expect_fail("v2.2 at most one Still-dark story", p, "at most one Still-dark story")
p = copy.deepcopy(SD); p["stories"].insert(0, p["stories"].pop())
expect_fail("v2.2 a Still-dark story never leads", p, "story 1 is the lead")

# the plan's fill order: new, then passed over (by days dark), then at most one Still dark; topic spread
FILL_ROWS = [row("rowOct10", "2026-10-10", "bundle", ["d1", "x1", "x2", "x3"]), row("rowOct12", "2026-10-12", "bundle", ["d2", "x4", "x5", "x6"]),
             row("rowNov1", "2026-11-01", "bundle", ["p1", "p2", "p3", "p4"])]
fs = lambda sid, seen, dd, **kw: story(sid, first_seen=seen, days_dark=dd, **kw)
pl = plan(dict(NOV5, ig_posts=FILL_ROWS, stories=[story("L", override=True), fs("n1", "2026-11-03", 5), fs("o1", "2026-10-25", 30),
                                                   fs("o2", "2026-10-20", 20), story("d1", days_dark=60), story("d2", days_dark=50)]))
record("v2.2 fill order: lead, new, then passed over by days dark",
       [(x["id"], x["slot"]) for x in pl["day"]["stories"]] == [("L", "lead"), ("n1", "new"), ("o1", "passed_over"), ("o2", "passed_over")],
       json.dumps(pl["day"]["stories"]))
pl = plan(dict(NOV5, ig_posts=FILL_ROWS, stories=[story("L", override=True), fs("n1", "2026-11-03", 5), fs("o1", "2026-10-25", 30),
                                                   story("d1", days_dark=60), story("d2", days_dark=50)]))
st = pl["day"]["stories"]
record("v2.2 a Still-dark filler (longest dark) takes the last slot, with its count line",
       [(x["id"], x["slot"]) for x in st] == [("L", "lead"), ("n1", "new"), ("o1", "passed_over"), ("d1", "still_dark")]
       and st[3].get("count") == "Still dark: day 60.", json.dumps(st))
pl = plan(dict(NOV5, ig_posts=FILL_ROWS, stories=[story("L", override=True), fs("n1", "2026-11-03", 5), story("d1", days_dark=60), story("d2", days_dark=50)]))
record("v2.2 at most one Still-dark story: two dark rows can't fill two slots",
       pl["day"]["format"] is None and [x["id"] for x in pl["day"]["stories"]] == ["L", "n1", "d1"], json.dumps(pl["day"])[:300])
pl = plan(dict(NOV5, ig_posts=[], stories=[story("L", override=True, topic="Gaza")] + [story(f"a{i}", topic="Gaza", days_dark=50 - i) for i in range(3)]
                                        + [story(f"b{i}", topic="Ukraine", days_dark=10 - i) for i in range(2)]))
record("v2.2 topic spread: no more than two from one topic while an alternative exists",
       [x["id"] for x in pl["day"]["stories"]] == ["L", "a0", "b0", "b1"] and "note" not in pl["day"], json.dumps(pl["day"])[:300])
pl = plan(dict(NOV5, ig_posts=[], stories=[story("L", override=True, topic="Gaza")] + [story(f"a{i}", topic="Gaza") for i in range(3)]))
record("v2.2 topic spread relaxed (and said so) when nothing else can fill the page",
       pl["day"]["format"] == "bundle" and "relaxed" in pl["day"].get("note", ""), json.dumps(pl["day"])[:300])

# §J: queued rows hold their slots; no two posts within 48 hours share an ask; incomplete rows reported
ASK_F, ASK_S = "Follow for the next one.", "Save this. Check back in a week."
qrows = [dict(row("rowNov5q", "2026-11-05", "bundle", ["z1"], slot="2026-11-05T08:00:00-05:00"), ask=ASK_F, flash=False),
         dict(row("rowNov6q", "2026-11-05", "deep", ["z2"], slot="2026-11-06T08:00:00-05:00"), ask=ASK_S, flash=True),
         {"id": "rowOld", "post_date": "2026-10-16", "format": None, "status": "Posted", "stories": [], "carousel_slot": None}]
pl = plan(dict(NOV5, ig_posts=qrows, stories=[story("s1")]))
record("J.1 the next slot comes after every queued slot (Sat 10am ET)", pl["next_slot"] == "2026-11-07T10:00:00-05:00", str(pl["next_slot"]))
record("J.4 asks of posts within 48 hours of the slot are blocked", pl["blocked_asks"] == [ASK_S], str(pl["blocked_asks"]))
record("J Flash counts the newest queued row", pl["last_flash"] is True, str(pl["last_flash"]))
record("J.2 rows missing Format or slot are reported, never filled",
       pl["incomplete_rows"] == [{"id": "rowOld", "missing": ["format", "carousel_slot"]}], str(pl["incomplete_rows"]))

# ---------- §G review page: download links ----------
# The day's post (four stories, Nov 5) and its companion on one page.
day = bundle4(date="2026-11-05")
code_d, log_d, d_day = render("F1-day", day)
calls_day = OUT / "F1-day-calls.json"; calls_day.write_text((FX / "2026-10-31-calls.json").read_text())
code, pages, log = review(OUT / "F1-day.json", d_day, calls_day, "--companion", str(FX / "2026-11-05-update.json"), str(UPD_CALLS))
html_ = pages[0].read_text() if pages else ""
media = sorted(f.name for f in d_day.iterdir() if f.suffix in (".png", ".mp4")) + sorted(f.name for f in d_u.iterdir() if f.suffix in (".png", ".mp4"))
missing = [m for m in media if m not in html_]
record("F1 day's post + Update companion on one review page",
       code_d == 0 and code == 0 and len(pages) == 1 and not missing and 'id="cap-1"' in html_ and 'id="rcap-1"' in html_,
       f"{len(pages)} page(s), missing={missing} " + (log or log_d).strip()[-200:])
no_dl = [m for m in media if f'href="{m}" download="{m}"' not in html_]
record("G review page: a download link for every MP4 and PNG (download attribute)", not media == [] and not no_dl, f"{len(media)} media, without a link: {no_dl}")
zips = re.findall(r'data-zip="([^"]+)" data-files="([^"]+)"', html_)
want = {"schmimknews-2026-11-05-bundle-slides.zip": 6, f"{stem_u}-slides.zip": 4}
record("G review page: a 'Download all slides' zip button per carousel, listing its PNGs",
       {z: len(f.split()) for z, f in zips} == want and html_.count(">Download all slides</button>") == 2, f"{zips}")
record("G review page: JSZip pinned from cdnjs", "https://cdnjs.cloudflare.com/ajax/libs/jszip/3.10.1/jszip.min.js" in html_)
record("G review page: 'Download video' and 'Download cover' under each Reel",
       html_.count(">Download video</a>") == 2 and html_.count(">Download cover</a>") == 2)
record("G review page: four story labels", all(f"Story {i} of 4" in html_ for i in range(1, 5)))
shutil.rmtree(d_day / "review", ignore_errors=True)
same_ask = copy.deepcopy(UPDATE); same_ask["ask"] = day["ask"]
sa = OUT / "F1-same-ask.json"; sa.write_text(json.dumps(same_ask, ensure_ascii=False))
code, _, log = review(OUT / "F1-day.json", d_day, calls_day, "--companion", str(sa), str(UPD_CALLS))
record("F1 companion with the day's ask refused", code != 0 and "day's ask" in log, log.strip()[-200:])
shutil.rmtree(d_day / "review", ignore_errors=True)

# ================= 0.4.0 the bundle (staged folder, zipped in the browser) =================
BZ_DAY, BZ_UPD = "2026-11-05_bundle01", "2026-11-05_update01"
STEM_DAY = "schmimknews-2026-11-05-bundle"

def bs(*args):
    """bundle_stage.py <post.json> <out_dir> <calls.json> <folder>, or bs("--check", <dir>)."""
    return subprocess.run([sys.executable, "-B", str(SCRIPTS / "bundle_stage.py"), *map(str, args)], capture_output=True, text=True)

def bcalls(name, base, reel=True, **extra):
    """A fresh calls JSON copied from `base` with no bundle fields (bundle_stage.py records them); optionally no reel_length."""
    cj = json.loads(Path(base).read_text()); cj.pop("bundle", None); cj.pop("bundle_files", None)
    cj.update(extra)
    if not reel: cj.pop("reel_length", None)
    p = OUT / name; p.write_text(json.dumps(cj)); return p

def calls_of(calls): return json.loads(Path(calls).read_text())

def staged_matches(d, folder, stem, n_slides, post, with_reel):
    """The staged folder has exactly the convention's files, media byte for byte the render's, captions the post's text + newline."""
    f = d / folder
    names = sorted(p.name for p in f.iterdir()) if f.is_dir() else []
    want = [f"slide_{i:02d}.png" for i in range(1, n_slides + 1)] + ["caption_carousel.txt"] + (["video.mp4", "caption_video.txt"] if with_reel else [])
    ok = names == sorted(want) and bundle_mod.layout_errors([f"{folder}/{n}" for n in names]) == []
    ok = ok and all((f / f"slide_{i:02d}.png").read_bytes() == (d / f"{stem}-{i:02d}.png").read_bytes() for i in range(1, n_slides + 1))
    ok = ok and (f / "caption_carousel.txt").read_bytes() == post["caption"].encode("utf-8") + b"\n"
    if with_reel:
        ok = ok and (f / "video.mp4").read_bytes() == (d / f"{stem}-reel.mp4").read_bytes()
        ok = ok and (f / "caption_video.txt").read_bytes() == post["reel_caption"].encode("utf-8") + b"\n"
    return ok, names

def check_stage(label, r, calls, folder, d, stem, n_slides, post, with_reel):
    """Record whether bs()'s result `r` staged <folder>/ in `d` as the convention says, printed its paths, left no .part,
    and recorded `bundle` and `bundle_files` in the calls JSON."""
    ok, names = staged_matches(d, folder, stem, n_slides, post, with_reel) if r.returncode == 0 else (False, [])
    cj = calls_of(calls)
    ok = ok and not list(d.glob("*.part")) and cj.get("bundle") == folder and sorted(cj.get("bundle_files") or []) == names \
         and r.stdout.split() == [f"{folder}/{n}" for n in cj.get("bundle_files") or []]
    record(label, ok, f"exit {r.returncode} {names} bundle={cj.get('bundle')} {(r.stdout + r.stderr).strip()[-200:]}")

# the day's bundle: six slides, a Reel, both captions
c_day = bcalls("bz-day-calls.json", calls_day)
r = bs(OUT / "F1-day.json", d_day, c_day, BZ_DAY)
check_stage("0.4.0 bundle: bundle post -> 2026-11-05_bundle01/ with slide_01-06.png, video.mp4 and both captions, bytes intact; paths printed; `bundle` and `bundle_files` recorded",
            r, c_day, BZ_DAY, d_day, STEM_DAY, 6, day, True)
(d_day / BZ_DAY / "old_slide.png").write_bytes(b"x")   # a stale file from an earlier run
r2 = bs(OUT / "F1-day.json", d_day, c_day, BZ_DAY)
record("0.4.0 bundle: staging again replaces the folder (a stale file is gone) and gives the same files",
       r2.returncode == 0 and r2.stdout == r.stdout and not (d_day / BZ_DAY / "old_slide.png").exists() and staged_matches(d_day, BZ_DAY, STEM_DAY, 6, day, True)[0])
r = bs("--check", d_day / BZ_DAY)
record("0.4.0 bundle: --check accepts the staged folder", r.returncode == 0 and r.stdout.strip() == "ok", (r.stdout + r.stderr).strip()[-200:])
bad_dir = OUT / BZ_DAY; shutil.rmtree(bad_dir, ignore_errors=True); shutil.copytree(d_day / BZ_DAY, bad_dir); (bad_dir / "notes.txt").write_text("x")
r = bs("--check", bad_dir)
record("0.4.0 bundle: --check refuses a stray file", r.returncode == 1 and "notes.txt' is not an allowed file name" in r.stdout, r.stdout.strip()[-200:])
r = bs("--check", OUT / "nonexistent-folder")
record("0.4.0 bundle: --check on a missing folder is a clean refusal, not a traceback", r.returncode != 0 and "is not a folder" in r.stdout + r.stderr and "Traceback" not in r.stderr, (r.stdout + r.stderr).strip()[-200:])

# a carousel-only run (no Reel rendered, no reel_length): the day's render folder minus its MP4 and staged folder
NO_STAGED = ("[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]_*", "review", ".reel-frames")   # copies start without a staged bundle
d_co = OUT / "bz-carousel-only"; shutil.rmtree(d_co, ignore_errors=True)
shutil.copytree(d_day, d_co, ignore=shutil.ignore_patterns(*NO_STAGED, "*.mp4"))
c_co = bcalls("bz-co-calls.json", calls_day, reel=False)
r = bs(OUT / "F1-day.json", d_co, c_co, BZ_DAY)
check_stage("0.4.0 bundle: carousel-only run has no video.mp4 and no caption_video.txt", r, c_co, BZ_DAY, d_co, STEM_DAY, 6, day, False)

# an Update companion
c_u = bcalls("bz-upd-calls.json", UPD_CALLS)
r = bs(FX / "2026-11-05-update.json", d_u, c_u, BZ_UPD)
check_stage("0.4.0 bundle: Update companion -> 2026-11-05_update01/ with 4 slides", r, c_u, BZ_UPD, d_u, stem_u, 4, UPDATE, True)

# refusals: nothing staged, the reason is named once, a stale staged folder and any bundle fields are removed
def refuse(name, post_json, src, folder, needle, mutate=None, absent=None):
    d = OUT / f"bz-{name}"; shutil.rmtree(d, ignore_errors=True)
    shutil.copytree(src, d, ignore=shutil.ignore_patterns(*NO_STAGED))
    if mutate: mutate(d)
    stale = d / BZ_DAY; stale.mkdir(); (stale / "slide_01.png").write_bytes(b"stale")   # an earlier staging that must not survive a refusal
    calls = bcalls(f"bz-{name}-calls.json".replace(" ", "-"), calls_day, bundle="2026-11-05_bundle09", bundle_files=["slide_01.png"])
    r = bs(post_json, d, calls, folder)
    out_ = r.stdout + r.stderr; cj = calls_of(calls)
    gone = (not stale.exists()) if folder == BZ_DAY else True   # only a valid folder name is ever cleaned up
    record(f"0.4.0 bundle refuses {name}",
           r.returncode == 1 and needle in out_ and (absent is None or absent not in out_) and not list(d.glob("*.part")) and gone
           and "bundle" not in cj and "bundle_files" not in cj, f"exit {r.returncode}, calls={sorted(cj)}: {out_.strip()[-200:]}")

DAYJ = OUT / "F1-day.json"
for name, folder, needle in (("a capital letter", "2026-11-05_Bundle01", "must read <YYYY-MM-DD>_"),
                             ("a hyphen before the format", "2026-11-05-bundle01", "must read <YYYY-MM-DD>_"),
                             ("no counter", "2026-11-05_bundle", "must read <YYYY-MM-DD>_"),
                             ("a trailing newline", "2026-11-05_bundle01\n", "must read <YYYY-MM-DD>_"),
                             ("counter 00", "2026-11-05_bundle00", "counter must be 01 or higher"),
                             ("another day's date", "2026-11-04_bundle01", "is not the post date 2026-11-05"),
                             ("another format", "2026-11-05_deep01", "is not the post format bundle"),
                             ("a path in the folder name", "../2026-11-05_bundle01", "must read <YYYY-MM-DD>_")):
    refuse(name, DAYJ, d_day, folder, needle)
refuse("a missing slide", DAYJ, d_day, BZ_DAY, "slide_03.png source missing", lambda d: (d / "schmimknews-2026-11-05-bundle-03.png").unlink(), absent="slide PNGs in")
refuse("a stray extra slide PNG", DAYJ, d_day, BZ_DAY, "7 slide PNGs", lambda d: shutil.copyfile(d / "schmimknews-2026-11-05-bundle-06.png", d / "schmimknews-2026-11-05-bundle-07.png"))
refuse("a missing video", DAYJ, d_day, BZ_DAY, "video.mp4 source missing", lambda d: (d / "schmimknews-2026-11-05-bundle-reel.mp4").unlink())
more_alt = OUT / "bz-more-alt.json"; more_alt.write_text(json.dumps(dict(day, alt=day["alt"] + ["one more"])))
refuse("more alt strings than slides", more_alt, d_day, BZ_DAY, "slide_07.png source missing")
no_rcap = OUT / "bz-no-rcap.json"; no_rcap.write_text(json.dumps(dict(day, reel_caption="")))
refuse("an empty Reel caption", no_rcap, d_day, BZ_DAY, "caption_video: the post has no text")
record("0.4.0 bundle: a non-string folder is reported, not raised",
       bundle_mod.folder_errors(5) != [] and bundle_mod.folder_errors(None) != [] and bundle_mod.folder_errors("2026-11-05_bundle01\n") != [])

# the layout check on bare name lists (what a hand-edited folder would look like)
G = [f"{BZ_DAY}/slide_01.png", f"{BZ_DAY}/slide_02.png", f"{BZ_DAY}/caption_carousel.txt"]
for name, names, needle in (("a stray cover file", G + [f"{BZ_DAY}/cover.png"], "not an allowed file name"),
                            ("a gap in the numbering", [G[0], f"{BZ_DAY}/slide_03.png", G[2]], "no gaps"),
                            ("numbering that doesn't start at 01", [f"{BZ_DAY}/slide_02.png", f"{BZ_DAY}/slide_03.png", G[2]], "no gaps"),
                            ("two root folders", G + ["2026-11-05_deep01/slide_01.png"], "exactly one root folder"),
                            ("a subfolder", G + [f"{BZ_DAY}/x/slide_09.png"], "not directly inside"),
                            ("a capitalised slide name", [G[0].replace("slide", "Slide"), G[1], G[2]], "not an allowed file name"),
                            ("slides named download1.png", [f"{BZ_DAY}/download1.png", f"{BZ_DAY}/download2.png", G[2]], "not an allowed file name"),
                            ("a video without its caption", G + [f"{BZ_DAY}/video.mp4"], "go together"),
                            ("no carousel caption", G[:2], "caption_carousel.txt is missing"),
                            ("no root folder", ["slide_01.png", "caption_carousel.txt"], "exactly one root folder"),
                            ("a newline in the folder name", [n.replace(BZ_DAY, BZ_DAY + "\n") for n in G], "must read"),
                            ("duplicate entries", G + [G[0]], "duplicate")):
    errs = bundle_mod.layout_errors(names)
    record(f"0.4.0 layout check flags {name}", any(needle in x for x in errs), f"{errs}")
record("0.4.0 layout check passes the convention, with and without a Reel",
       bundle_mod.layout_errors(G) == [] and bundle_mod.layout_errors(G + [f"{BZ_DAY}/video.mp4", f"{BZ_DAY}/caption_video.txt"]) == [])

# the review page: a bundle button only when bundle_stage.py recorded `bundle` and `bundle_files`; every download saves via the capability
def page(*args):
    """Build the day's review page; return (exit code, its HTML, log), and clear the page folder."""
    code, pages, log = review(DAYJ, d_day, *args)
    html_ = pages[0].read_text() if pages else ""
    shutil.rmtree(d_day / "review", ignore_errors=True)
    return code, html_, log.strip()[-200:]

want_files = " ".join(f"{BZ_DAY}/{n}" for n in calls_of(c_day)["bundle_files"])
code, html_, log = page(c_day)
record("0.4.0 review page: 'Download bundle zip' button zips <bundle>/<file> for every staged file and names the zip <bundle>.zip",
       code == 0 and f'<button type="button" class="dl dl-zip dl-bundle" data-zip="{BZ_DAY}.zip" data-files="{want_files}">Download bundle zip</button>' in html_
       and html_.count("Download bundle zip") == 1 and ">Download all slides</button>" in html_, log)
record("0.4.0 review page: downloads go through the `downloads` capability (with a plain-browser fallback)",
       "claude.use('downloads')" in html_ and "DL.save(" in html_ and "createObjectURL" in html_ and "a[download]" in html_)
code, html_, log = page(c_day, "--companion", str(FX / "2026-11-05-update.json"), str(c_u))
record("0.4.0 review page: the Update companion gets its own bundle button",
       code == 0 and f'data-zip="{BZ_UPD}.zip"' in html_ and f'data-zip="{BZ_DAY}.zip"' in html_ and html_.count(">Download bundle zip</button>") == 2, log)
code, html_, log = page(calls_day)
record("0.4.0 review page: no `bundle` in the calls, no bundle button, the rest unchanged",
       code == 0 and "bundle zip" not in html_.lower() and html_.count(">Download all slides</button>") == 1, log)
for label, extra in (("a javascript: URL", {"bundle": "javascript:alert(1)//", "bundle_files": ["slide_01.png"]}),
                     ("an off-site URL", {"bundle": "https://evil.example/x", "bundle_files": ["slide_01.png"]}),
                     ("a non-string", {"bundle": 5, "bundle_files": ["slide_01.png"]}),
                     ("a hostile file name", {"bundle": BZ_DAY, "bundle_files": ['x"><script>alert(1)</script>.png']}),
                     ("a path in a file name", {"bundle": BZ_DAY, "bundle_files": ["../slide_01.png"]}),
                     ("no file list", {"bundle": BZ_DAY}),
                     ("an empty file list", {"bundle": BZ_DAY, "bundle_files": []})):
    code, html_, log = page(bcalls("bz-hostile-calls.json", calls_day, **extra))
    record(f"0.4.0 review page: hostile or incomplete bundle fields ({label}) give no bundle button and no crash",
           code == 0 and "Download bundle zip" not in html_ and "evil.example" not in html_ and "javascript:" not in html_ and "<script>alert" not in html_, log)

# a real browser runs the page's own JavaScript: the zip it builds and the saves it makes (needs Playwright and the cdnjs JSZip, as production does)
flat = OUT / "bz-browser"; shutil.rmtree(flat, ignore_errors=True)
shutil.copytree(d_day, flat, ignore=shutil.ignore_patterns("review", ".reel-frames"))
code, pages, log = review(DAYJ, flat, c_day)   # writes flat/review/...; the browser needs the page beside its files
(flat / "review" / pages[0].name).replace(flat / pages[0].name) if pages else None
br = subprocess.run([A.python, "-B", str(HERE / "check_page_downloads.py"), str(flat), f"dead-air-2026-11-05.html", BZ_DAY], capture_output=True, text=True, timeout=300)
try: res = json.loads(br.stdout.strip().splitlines()[-1])
except Exception: res = {"error": f"no result: {(br.stdout + br.stderr).strip()[-300:]}"}
staged_sha = {p.name: sha(p) for p in (flat / BZ_DAY).iterdir()}
saves = (res.get("cap") or {}).get("saves") or []
zsave = next((s for s in saves if s["filename"] == f"{BZ_DAY}.zip"), None)
record("0.4.0 browser: the bundle zip is built from the published folder and handed to downloads.save, every entry byte for byte",
       bool(zsave) and zsave["entries"] == {f"{BZ_DAY}/{n}": h for n, h in staged_sha.items()}, res.get("error") or f"saves={[s['filename'] for s in saves]}")
vsave = next((s for s in saves if s["filename"] == f"{STEM_DAY}-reel.mp4"), None)
record("0.4.0 browser: 'Download video' saves the MP4 through downloads.save, byte for byte",
       bool(vsave) and vsave["sha"] == sha(flat / f"{STEM_DAY}-reel.mp4"), res.get("error") or "")
asave = next((s for s in saves if s["filename"] == f"{STEM_DAY}-slides.zip"), None)
record("0.4.0 browser: 'Download all slides' zips the six PNGs and saves it through downloads.save",
       bool(asave) and asave["entries"] == {f"{STEM_DAY}-{i:02d}.png": sha(flat / f"{STEM_DAY}-{i:02d}.png") for i in range(1, 7)}, res.get("error") or "")
dc = res.get("decline") or {}
record("0.4.0 browser: a declined save saves nothing and restores the button without an error",
       dc.get("saves") == [] and dc.get("label_after") == dc.get("label_before") and "download bundle zip" in (dc.get("label_after") or "").lower(),   # CSS upper-cases the label
       res.get("error") or str(dc))
nc = res.get("nocap") or {}
record("0.4.0 browser: with no capability the browser's own download is the fallback, and the zip it makes is valid",
       nc.get("video_name") == f"{STEM_DAY}-reel.mp4" and nc.get("zip_name") == f"{BZ_DAY}.zip" and nc.get("testzip") is None
       and sorted(n for n in nc.get("names") or [] if not n.endswith("/")) == sorted(f"{BZ_DAY}/{n}" for n in staged_sha)
       and {n for n in nc.get("names") or [] if n.endswith("/")} <= {f"{BZ_DAY}/"}, res.get("error") or str(nc))   # JSZip may add the folder's own entry

# ---------- §E.1 / §C versions agree ----------
pver = json.loads((PLUGIN / ".claude-plugin/plugin.json").read_text())["version"]
cver = {c.name: re.findall(r"^DEAD_AIR_VERSION=(\S+)$", c.read_text(), re.M) for c in COMMANDS}
mver = [x["version"] for x in json.loads((REPO / ".claude-plugin/marketplace.json").read_text())["plugins"] if x["name"] == "dead-air"]
record("E.1 DEAD_AIR_VERSION matches plugin.json in all three commands (and marketplace.json)",
       len(COMMANDS) == 3 and all(v == [pver] for v in cver.values()) and mver == [pver], f"plugin {pver}, commands {cver}, marketplace {mver}")

# ---------- §A / §H setup block ----------
BLOCK = re.compile(r"(# --- dead-air setup:.*?# --- end dead-air setup ---)", re.S)
blocks = {c.name: BLOCK.findall(c.read_text()) for c in COMMANDS}
record("A the setup block is identical in all three commands",
       all(len(b) == 1 for b in blocks.values()) and len({b[0] for b in blocks.values()}) == 1, f"{ {k: len(v) for k, v in blocks.items()} }")
SESSION_PATH = re.compile(r"/root/\.claude|/home/[^/\s]+/\.claude|synced/(?!\*)[^\s/`'\"]+|[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-")
hard = [f"{c.name}:{i}" for c in COMMANDS for i, line in enumerate(c.read_text().splitlines(), 1) if SESSION_PATH.search(line)]
record("H.1 no hard-coded session path in any command", not hard, f"{hard}")

def run_setup(home, repo_url):
    """Run the commands' setup block in a scratch working dir with its own HOME; return its KEY=value lines."""
    wd = OUT / "setup-wd"; shutil.rmtree(wd, ignore_errors=True); wd.mkdir()
    env = dict(os.environ, HOME=str(home), DEAD_AIR_REPO=repo_url); env.pop("CLAUDE_PLUGIN_ROOT", None)
    r = subprocess.run(["bash", "-c", next(iter(blocks.values()))[0]], cwd=wd, env=env, capture_output=True, text=True, timeout=120)
    return dict(l.split("=", 1) for l in r.stdout.splitlines() if "=" in l)

def plugin_copy(dst, version):
    shutil.copytree(PLUGIN, dst, ignore=shutil.ignore_patterns("tests", "__pycache__"))
    pj = dst / ".claude-plugin/plugin.json"; pj.write_text(json.dumps(dict(json.loads(pj.read_text()), version=version)))

H = OUT / "setup-home"; shutil.rmtree(H, ignore_errors=True)
plugin_copy(H / ".claude/plugins/synced/aaaa/dead-air", "0.1.0")
plugin_copy(H / ".claude/plugins/synced/bbbb/dead-air~g2", pver)
plugin_copy(H / ".claude/plugins/synced/cccc/dead-air~g3", "9.9.9")
out = run_setup(H, "file:///nonexistent")
record("H.2 several synced copies: the one whose version equals DEAD_AIR_VERSION wins, never the first match",
       out.get("DA_ROOT", "").endswith("bbbb/dead-air~g2") and out.get("DA_FROM") == f"local install {pver}", f"{out}")
shutil.rmtree(H / ".claude/plugins/synced/bbbb")
GIT = OUT / "setup-repo"; shutil.rmtree(GIT, ignore_errors=True)
plugin_copy(GIT / "plugins/dead-air", pver)
git = lambda *a: subprocess.run(["git", "-C", str(GIT), "-c", "user.name=t", "-c", "user.email=t@t", *a], capture_output=True, text=True)
git("init", "-q", "-b", "main"); git("add", "-A"); git("commit", "-qm", "fixture")
record("A step 1 fails on a version mismatch, and so does an unreachable repo: unresolved",
       run_setup(H, "file:///nonexistent").get("DA_ROOT") == "unresolved")
out = run_setup(H, f"file://{GIT}")
record("A step 2: no tag -> main, recorded as a version mismatch with its SHA",
       out.get("DA_FROM", "").startswith("version mismatch: ran main at ") and out.get("DA_ROOT", "").endswith("src/repo/plugins/dead-air"), f"{out}")
git("tag", f"dead-air-v{pver}")
out = run_setup(H, f"file://{GIT}")
sha_ = git("rev-parse", "HEAD").stdout.strip()
record("A step 2: the release tag is fetched into dead-air/src, version-checked",
       out.get("DA_FROM") == f"repo tag dead-air-v{pver}" and out.get("DA_COMMIT") == sha_
       and (Path(out.get("DA_ROOT", "/x")) / "scripts/render.py").is_file(), f"{out}")

# ---------- §E.2-3 the cache manifest ----------
C = OUT / "cache-check"; shutil.rmtree(C, ignore_errors=True)
root = OUT / "cache-root"; shutil.rmtree(root, ignore_errors=True); plugin_copy(root, pver)
(root / "scripts/__pycache__").mkdir(exist_ok=True); (root / "scripts/__pycache__/x.pyc").write_bytes(b"x")
for top in ("scripts", "references", "agents"): shutil.copytree(root / top, C / top)
r = subprocess.run([sys.executable, "-B", str(SCRIPTS / "cache_manifest.py"), str(root), str(C / "VERSION"), "--commit", "abc123", "--date", "2026-11-05"],
                   capture_output=True, text=True)
ver = (C / "VERSION").read_text() if (C / "VERSION").exists() else ""
check = lambda: subprocess.run(["bash", "-c", "sed '1,/^files$/d' VERSION | sha256sum -c --quiet"], cwd=C, capture_output=True, text=True).returncode
record("E.2 cache VERSION: version, commit, date, every mirrored file, no bytecode",
       r.returncode == 0 and ver.startswith(f"dead-air {pver}\ncommit abc123\ndate 2026-11-05\nfiles\n")
       and "  scripts/render.py\n" in ver and "  references/editorial-rules.md\n" in ver and "  agents/dead-air-qa.md\n" in ver
       and "__pycache__" not in ver, ver[:200])
record("E.2 a matching cache verifies with sha256sum -c alone", check() == 0)
(C / "references/editorial-rules.md").write_text("tampered")
record("E.3 a changed cached file fails the checksum (the run stops)", check() != 0)

# ---------- §E.4 / §B no command writes under settings/ or dev/; §I python3 -B everywhere ----------
WRITE = re.compile(r"project_write|upload|>\s*\S*dead-air/|writes?\b(?! it)", re.I)
bad = [f"{c.name}:{i}" for c in COMMANDS for i, line in enumerate(c.read_text().splitlines(), 1)
       if re.search(r"dead-air/(settings|dev)/", line) and WRITE.search(line) and not re.search(r"\*\*never|never writes|never write", line, re.I)]
record("E.4 no command writes under settings/ or dev/", not bad, f"{bad}")
texts = [c for c in COMMANDS] + sorted((PLUGIN / "references").glob("*.md")) + sorted((PLUGIN / "agents").glob("*.md")) + [PLUGIN / "README.md", HERE / "run-fixture.sh"]
no_b = [f"{t.name}:{i}" for t in texts for i, line in enumerate(t.read_text().splitlines(), 1)
        if (re.search(r"(?<![\w-])python3\s+(?!-B)(?!-m venv)\S", line) or re.search(r'^\s*"\$PY"\s+(?!-B)', line))]
record("I.1 every script runs as python3 -B (commands, references, agents, README, test runner)", not no_b, f"{no_b}")
shutil.rmtree(root, ignore_errors=True); shutil.rmtree(C, ignore_errors=True)   # the deliberate __pycache__ above
pyc = [str(x) for x in PLUGIN.rglob("__pycache__")]
record("I.1 no __pycache__ left in the plugin after the test run", not pyc, f"{pyc}")

# ---------- summary ----------
failed = [r for r in results if not r[1]]
print(f"\n{len(results) - len(failed)}/{len(results)} passed")
sys.exit(1 if failed else 0)
