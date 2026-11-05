#!/usr/bin/env python3
"""Dead Air · the day's plan from the dashboard (SPEC §8.1-8.2 with addenda v2.1 and v2.2). Stdlib only.

  python3 -B plan_day.py <rows.json>      prints the plan as JSON

/dead-air phase 2 writes <rows.json> from what phase 1 read (post-schema §3 has the shape):
  {"run_date": "YYYY-MM-DD", "now": "<ISO datetime with offset>", "format_override": null | "bundle" | "weekly",
   "ig_posts": [{"id", "post_date", "format", "status", "carousel_slot", "stories": [record ids], "flash", "ask"}],
   "stories":  [{"id", "status", "confirmation", "days_dark", "silent", "topic", "first_seen", "override", "hold",
                 "first_pickup": {"outlet", "date"} | null}]}

It decides only what the rules decide mechanically: which rows count as posted (queued ones included), which
stories are eligible and in what order, the day's four stories (lead, then new, passed-over and Still-dark
fillers), which Covered stories become Update companions and which are corrections, the next open carousel
slot and the asks it can't use. Counting questions (`hold`), the override test (`override`), the first
pickup's date and Flash stay judgment calls the agent makes and logs.
"""
import json, sys
from datetime import date, datetime, time, timedelta, timezone

CONF = {"Verified": 0, "Probable": 1}
DAY_FORMATS = ("single", "bundle", "weekly", "deep")
STORIES_PER_POST = 4          # addendum v2.2 §F.1: every daily carousel and every weekly carries four
MAX_PER_TOPIC = 2             # §F.5
STILL_DARK_AFTER = 14         # §F.3c: posted before, but not in the last 14 days
ASK_GAP = timedelta(hours=48) # §J.4

def d(s): return date.fromisoformat(s[:10])

def dt(s, field):
    """ISO datetime with an offset. Accepts Airtable's UTC form ('…Z'), which fromisoformat rejects before 3.11."""
    try: v = datetime.fromisoformat(s[:-1] + "+00:00" if s.endswith("Z") else s)
    except ValueError: sys.exit(f"{field}: {s!r} is not an ISO datetime")
    if v.tzinfo is None: sys.exit(f"{field}: {s!r} has no UTC offset (write e.g. -05:00 or Z)")
    return v

def eastern(now):
    """US Eastern, or the offset `now` was given in if the zone database is missing."""
    try:
        from zoneinfo import ZoneInfo
        return ZoneInfo("America/New_York")
    except Exception:
        return now.tzinfo or timezone(timedelta(hours=-5))

def rank_key(s, ever):
    """§8.2: never posted first, Verified before Probable, days dark, outlets checked silent."""
    return (CONF[s["confirmation"]], s["id"] in ever, -s.get("days_dark", 0), -s.get("silent", 0))

def pick_fillers(lead, groups, need):
    """§F.3-5: fill the slots after the lead from the groups in order, at most one Still-dark story, and at most
    two stories per topic while an alternative exists. Returns (picked [(story, group)], topic_note or None)."""
    picked, topics = [], {}
    if lead.get("topic"): topics[lead["topic"]] = 1
    ordered = [(s, g) for g, ss in groups for s in ss]
    def take(allow_crowd):
        for s, g in ordered:
            if len(picked) == need: return
            if any(s["id"] == p["id"] for p, _ in picked): continue
            if g == "still_dark" and any(pg == "still_dark" for _, pg in picked): continue
            t = s.get("topic")
            if t and topics.get(t, 0) >= MAX_PER_TOPIC and not allow_crowd: continue
            picked.append((s, g))
            if t: topics[t] = topics.get(t, 0) + 1
    take(False)
    note = None
    if len(picked) < need:
        n = len(picked); take(True)
        if len(picked) > n: note = "topic spread relaxed: no alternative outside a topic that already had two stories"
    return picked, note

def next_slot(rows, now, run):
    """§J.1: the next morning slot (8:00am ET weekdays, 10:00am ET weekends) on or after the run date that is still
    ahead and not held by any IG Posts row, queued ones included."""
    tz = eastern(now)
    held = set()
    for r in rows:
        if r.get("carousel_slot"):
            s = dt(r["carousel_slot"], f"{r['id']} carousel_slot").astimezone(tz)
            if s.hour < 12: held.add(s.date())
    day = run
    for _ in range(60):
        t = datetime.combine(day, time(10 if day.weekday() >= 5 else 8), tz)
        if t > now and day not in held: return t
        day += timedelta(days=1)
    return None

def plan(inp):
    run, now = d(inp["run_date"]), dt(inp["now"], "now")
    override = inp.get("format_override")
    if override not in (None, "bundle", "weekly"):
        sys.exit(f"format_override {override!r}: /dead-air builds a bundle or a weekly (addendum v2.2 §F.1)")
    all_rows = inp["ig_posts"]
    rows = [r for r in all_rows if r.get("status") != "Skipped"]
    # §0 + v2.2 §J.1: Posted counts; a Ready row counts too, whether its slot has passed (assumed posted) or is
    # still ahead (queued: it holds its slot and its stories, Flash and ask).
    posted, assumed, queued, stale, incomplete = [], [], [], [], []
    for r in all_rows:
        miss = [k for k in ("format", "carousel_slot") if not r.get(k)]
        if miss: incomplete.append({"id": r["id"], "missing": miss})
    for r in rows:
        slot = dt(r["carousel_slot"], f"{r['id']} carousel_slot") if r.get("carousel_slot") else None
        if r["status"] == "Posted": posted.append(r)
        elif r["status"] == "Ready":
            posted.append(r)
            if slot and slot >= now: queued.append(r["id"])
            else:
                assumed.append(r["id"])
                if slot and now - slot > timedelta(days=7): stale.append({"id": r["id"], "slot": r["carousel_slot"], "days_past": (now - slot).days})
    posted.sort(key=lambda r: (r["post_date"], r.get("carousel_slot") or ""), reverse=True)
    within = lambda r, n: run - d(r["post_date"]) < timedelta(days=n)

    # Eligibility (§8.2). The 7-day no-repeat rule is kept apart: the weekly is its one exception.
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
    pool.sort(key=lambda s: rank_key(s, ever))
    fresh = [s for s in pool if s["id"] not in recent]

    # The day's post (§F.1): a bundle of four, or the weekly on a Sunday. Update rows are never "the last post".
    day_rows = [r for r in posted if r["format"] in DAY_FORMATS]
    weekly_due = run.weekday() == 6 and not any(r["format"] == "weekly" and within(r, 7) for r in rows)
    if override: fmt, why = override, f"--format {override}"
    elif weekly_due: fmt, why = "weekly", "rule 3: Sunday, no weekly in the last 6 days"
    else: fmt, why = "bundle", "every daily carousel is a bundle of four (addendum v2.2 §F.1)"
    base = pool if fmt == "weekly" else fresh   # the weekly may repeat this week's stories
    lead = next((s for s in base if s.get("override")), None)
    lead_why = "rule 2: Verified, all 11 checked and silent since the last post" if lead else "top of the §8.2 ranking"
    lead = lead or (base[0] if base else None)
    slots, note, unfilled = [], None, []
    if lead:
        slots.append({"id": lead["id"], "slot": "lead", "why": lead_why})
        rest = [s for s in base if s["id"] != lead["id"]]
        if fmt == "weekly":
            groups = [("week", rest)]
        else:
            # §F.3: a new rows (never posted, first seen since the last daily post), b rows passed over on earlier
            # days (never posted, already there at the last daily post), c Still dark (posted, not in 14 days).
            last_day = d(day_rows[0]["post_date"]) if day_rows else None
            never = [s for s in rest if s["id"] not in ever]
            passed = [s for s in never if last_day and s.get("first_seen") and d(s["first_seen"]) < last_day]
            new = [s for s in never if s not in passed]
            dark = sorted((s for s in rest if s["id"] in ever and not any(s["id"] in r["stories"] for r in posted if within(r, STILL_DARK_AFTER))),
                          key=lambda s: -s.get("days_dark", 0))
            groups = [("new", new), ("passed_over", sorted(passed, key=lambda s: -s.get("days_dark", 0))), ("still_dark", dark)]
        picked, note = pick_fillers(lead, groups, STORIES_PER_POST - 1)
        slots += [{"id": s["id"], "slot": g, **({"count": f"Still dark: day {s.get('days_dark')}."} if g == "still_dark" else {})}
                  for s, g in picked]
    if len(slots) < STORIES_PER_POST:
        unfilled = [f"slot {i + 1}: " + ("no eligible lead" if i == 0 else
                    "no new, passed-over or Still-dark row left (Provisional, held, Covered and last-7-days rows never fill)")
                    for i in range(len(slots), STORIES_PER_POST)]
    if fmt != "weekly":
        skipped += [{"id": s["id"], "reason": "posted in the last 7 days"} for s in pool if s["id"] in recent]
    if len(slots) == STORIES_PER_POST:
        day = {"format": fmt, "rule": why, "stories": slots, "eligible": [s["id"] for s in base], "skipped": skipped}
        if note: day["note"] = note
    else:
        # §F.6: no carousel; the lead's Reel still runs on its own, as a standalone deep post.
        day = {"format": None, "rule": f"fewer than {STORIES_PER_POST} qualifying stories: no carousel today",
               "unfilled": unfilled, "reel_only": lead["id"] if lead else None, "stories": slots,
               "eligible": [s["id"] for s in base], "skipped": skipped}

    # Updates (§A.2) vs corrections (§C), against the latest post that carried each story.
    updated = {sid for r in rows if r["format"] == "update" for sid in r["stories"]}
    latest = {}
    for r in reversed(posted):          # oldest first, so the newest post wins
        if r["format"] in DAY_FORMATS and within(r, 30) and r["id"] not in queued:
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

    # Slots, Flash and asks (§J): queued rows hold their slots, and no two posts within 48 hours share an ask.
    slot = next_slot(rows, now, run)
    near = [r for r in rows if r.get("ask") and r.get("carousel_slot") and slot
            and abs(dt(r["carousel_slot"], r["id"]) - slot) < ASK_GAP]
    blocked = sorted({r["ask"] for r in near} | ({day_rows[0]["ask"]} if day_rows and day_rows[0].get("ask") else set()))
    return {"posted_rule": "Posted rows, and Ready rows whatever their slot, count as posted (v2.1 §D, v2.2 §J.1).",
            "assumed_posted": assumed, "queued": queued, "stale_ready": stale, "incomplete_rows": incomplete,
            "day": day, "next_slot": slot.isoformat() if slot else None,
            "taken_slots": sorted(r["carousel_slot"] for r in rows if r.get("carousel_slot") and dt(r["carousel_slot"], r["id"]) >= now),
            "blocked_asks": blocked, "last_flash": bool(posted[0].get("flash")) if posted else False,
            "companions": updates[:2], "deferred_updates": updates[2:],
            "corrections": corrections, "unresolved": unresolved}

if __name__ == "__main__":
    if len(sys.argv) != 2: print(__doc__); sys.exit(2)
    print(json.dumps(plan(json.load(open(sys.argv[1]))), indent=2))
