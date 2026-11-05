#!/usr/bin/env python3
"""Dead Air · the day's plan from the dashboard (SPEC §8.1-8.2 with addendum v2.1 §A, §C, §D). Stdlib only.

  python3 plan_day.py <rows.json>      prints the plan as JSON

/dead-air phase 2 writes <rows.json> from what phase 1 read (post-schema §3 has the shape):
  {"run_date": "YYYY-MM-DD", "now": "<ISO datetime with offset>", "format_override": null | "single" | ...,
   "ig_posts": [{"id", "post_date", "format", "status", "carousel_slot", "stories": [record ids]}],
   "stories":  [{"id", "status", "confirmation", "days_dark", "silent", "override", "hold",
                 "first_pickup": {"outlet", "date"} | null}]}

It decides only what the rules decide mechanically: which rows count as posted, which stories are eligible
and in what order, the day's format, which Covered stories become Update companions and which are
corrections. Counting questions (`hold`), the override test (`override`), the first pickup's date, Flash,
the ask and the slots stay judgment calls the agent makes and logs.
"""
import json, sys
from datetime import date, datetime, timedelta

CONF = {"Verified": 0, "Probable": 1}
DAY_FORMATS = ("single", "bundle", "weekly", "deep")

def d(s): return date.fromisoformat(s[:10])

def dt(s, field):
    """ISO datetime with an offset. Accepts Airtable's UTC form ('…Z'), which fromisoformat rejects before 3.11."""
    try: v = datetime.fromisoformat(s[:-1] + "+00:00" if s.endswith("Z") else s)
    except ValueError: sys.exit(f"{field}: {s!r} is not an ISO datetime")
    if v.tzinfo is None: sys.exit(f"{field}: {s!r} has no UTC offset (write e.g. -05:00 or Z)")
    return v

def plan(inp):
    run, now = d(inp["run_date"]), dt(inp["now"], "now")
    rows = [r for r in inp["ig_posts"] if r.get("status") != "Skipped"]
    # §D: Imran rarely flips Status to Posted, so a Ready row whose slot has passed counts as posted.
    posted, assumed, stale = [], [], []
    for r in rows:
        slot = dt(r["carousel_slot"], f"{r['id']} carousel_slot") if r.get("carousel_slot") else None
        if r["status"] == "Posted": posted.append(r)
        elif r["status"] == "Ready" and slot and slot < now:
            posted.append(r); assumed.append(r["id"])
            if now - slot > timedelta(days=7): stale.append({"id": r["id"], "slot": r["carousel_slot"], "days_past": (now - slot).days})
    posted.sort(key=lambda r: r["post_date"], reverse=True)
    within = lambda r, n: run - d(r["post_date"]) < timedelta(days=n)

    # Eligibility (§8.2) and ranking. The 7-day no-repeat rule is kept apart: the weekly is its one exception.
    stories = {s["id"]: s for s in inp["stories"]}
    ever = {sid for r in posted for sid in r["stories"]}
    pool, recent, skipped = [], set(), []
    for s in inp["stories"]:
        if s["status"] != "Flagged": continue
        n14 = sum(s["id"] in r["stories"] for r in posted if within(r, 14))
        reason = (None if s.get("confirmation") in CONF else f"confirmation {s.get('confirmation')} never posts")
        reason = reason or (f"held: {s['hold']}" if s.get("hold") else None)
        reason = reason or ("already in two posts in the last 14 days" if n14 >= 2 else None)
        if reason: skipped.append({"id": s["id"], "reason": reason}); continue
        pool.append(s)
        if any(s["id"] in r["stories"] for r in posted if within(r, 7)): recent.add(s["id"])
    pool.sort(key=lambda s: (CONF[s["confirmation"]], s["id"] in ever, -s.get("days_dark", 0), -s.get("silent", 0)))
    fresh = [s for s in pool if s["id"] not in recent]

    # The day's format, §8.1 rules 2-5, as if no Update were due (§A.1). Update rows never count as "the last post".
    day_rows = [r for r in posted if r["format"] in DAY_FORMATS]
    last = day_rows[0]["format"] if day_rows else None
    override = inp.get("format_override")
    if override: fmt, why = override, "--format override"
    elif any(s.get("override") for s in fresh): fmt, why = "single", "rule 2: override (Verified, all 11 checked and silent since the last post)"
    elif run.weekday() == 6 and not any(r["format"] == "weekly" and within(r, 7) for r in rows): fmt, why = "weekly", "rule 3: Sunday, no weekly in the last 6 days"
    elif last in ("bundle", "weekly"): fmt, why = "single", f"rule 4: alternate (last post was a {last})"
    elif last in ("single", "deep"): fmt, why = "bundle", f"rule 4: alternate (last post was a {last})"
    else: fmt, why = "single", "rule 4: no earlier post to alternate from"
    eligible = pool if fmt == "weekly" else fresh   # the weekly may repeat this week's stories
    if fmt in ("bundle", "weekly") and len(eligible) < 3:
        why = (f"--format {fmt} overridden by " if override else "") + f"rule 5: fallback ({len(eligible)} eligible, a {fmt} needs 3)"
        fmt, eligible = "single", fresh
    if fmt != "weekly":
        skipped += [{"id": s["id"], "reason": "posted in the last 7 days"} for s in pool if s["id"] in recent]
    if fmt == "single" and any(s.get("override") for s in eligible):
        eligible = sorted(eligible, key=lambda s: not s.get("override"))   # the override story leads
    day = ({"format": fmt, "rule": why, "eligible": [s["id"] for s in eligible], "skipped": skipped} if eligible
           else {"format": None, "rule": "no eligible story", "eligible": [], "skipped": skipped})

    # Updates (§A.2) vs corrections (§C), against the latest post that carried each story.
    updated = {sid for r in rows if r["format"] == "update" for sid in r["stories"]}
    latest = {}
    for r in reversed(posted):          # oldest first, so the newest post wins
        if r["format"] in DAY_FORMATS and within(r, 30):
            for sid in r["stories"]: latest[sid] = r
    updates, corrections, unresolved = [], [], []
    for sid, r in latest.items():
        s = stories.get(sid)
        if not s or s["status"] != "Covered" or sid in updated: continue
        p = s.get("first_pickup")
        if not p: unresolved.append({"story": sid, "post": r["id"], "reason": "Covered, but no first-pickup date"}); continue
        item = {"story": sid, "post": r["id"], "posted": r["post_date"], "outlet": p["outlet"], "pickup": p["date"]}
        if d(p["date"]) <= d(r["post_date"]):
            corrections.append(dict(item, line=f"Correction due: {sid}, posted {r['post_date']}, said {p['outlet']} hadn't run it; "
                                                f"{p['outlet']} ran it {p['date']}."))
        else: updates.append(item)
    updates.sort(key=lambda u: u["pickup"])
    return {"posted_rule": "Ready rows whose carousel slot has passed count as posted (addendum v2.1 §D).",
            "assumed_posted": assumed, "stale_ready": stale, "day": day,
            "companions": updates[:2], "deferred_updates": updates[2:],
            "corrections": corrections, "unresolved": unresolved}

if __name__ == "__main__":
    if len(sys.argv) != 2: print(__doc__); sys.exit(2)
    print(json.dumps(plan(json.load(open(sys.argv[1]))), indent=2))
