#!/usr/bin/env python3
"""SPEC §13 acceptance tests 1-7a for the dead-air renderer, against the bundled fixtures.

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
         and mp4.exists() and cover.exists()
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
      and secs is not None and 50.5 <= secs <= 53.5)
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

# ---------- summary ----------
failed = [r for r in results if not r[1]]
print(f"\n{len(results) - len(failed)}/{len(results)} passed")
sys.exit(1 if failed else 0)
