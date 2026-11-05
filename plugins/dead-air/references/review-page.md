# Review page

SPEC §5.3 and §10.1, with addendum v2.1 §A. Every day's post gets its own dated review page: a **new** claude.ai artifact per post. Never republish over an earlier post's page. **Update companions are the exception:** they go on the day's page, not a page of their own.

## What it shows

`review_page.py` builds the page. In order, it shows:

1. A header and facts strip: the calls JSON's `facts`.
2. **The Reel first:** the MP4, with the cover as its poster, plus its headline.
3. **The carousel strip:** every slide in posting order, each with its label and alt text.
4. **Both captions,** each with a Copy button.
5. **The stories in the post:** title or headline, record ID, dateline, count or stat, confidence.
6. **The calls:** every judgment from the calls JSON.
7. **Each Update companion** (if any), under an amber rule: its own facts strip, then 2–6 for the companion, with its own Copy buttons.

It is a single dark page in the feed's own look. It loads Google Fonts for its own type; that request is allowed on a published artifact, unlike in the render workspace.

## Building and publishing

```
python3 review_page.py <post.json> <out_dir> <calls.json> [--companion <update.json> <update-calls.json>]... [--title …] [--h1 …] [--name …]
```

- Run it with `<out_dir>` set to the render folder, so the HTML and the media files sit side by side. It prints the path of the HTML it wrote.
- **Dashboard posts:** no flags. The title is "Dead Air <Mon D>", the h1 is "Dead Air · <Mon D YYYY>", and the file is `dead-air-<date>.html`.
- **Update companions:** pass each with `--companion`, oldest pickup first, at most two. The script refuses a companion dated differently from the day's post or using its ask.
- **Standalone deep posts (`/dead-air-reel`):** `--title "Dead Air: <Slug>"`, `--h1 "Dead Air · <The subject>"`, `--name dead-air-<slug>`.
- Every post renders into its own `dead-air/out/<name>/` folder, so a second post on the same day (the second Reel's deep post, or a `-v2` re-cut) never overwrites the first one's files.

**Publish** with the Artifact tool:
- Load the `artifact-design` skill before the first publish of a session.
- `file_path` is the HTML. `files` maps every carousel PNG, the `-reel.mp4` and the `-reel-cover.png` to themselves by filename; the page references them by bare filename. With companions, `files` also maps each companion's PNGs, MP4 and cover from its own `dead-air/out/<date>-update-<slug>/` folder; the slug in their names keeps them apart. Don't publish `checks.json` or `.reel-frames/`.
- Each post is a new artifact with a new path; don't pass `url`.
- Keep the returned link: it goes in the post's `.md`, the IG Posts row and the report. A companion's `.md` and IG Posts row carry the same link.

If the Artifact tool can't publish, follow [render-guide.md](render-guide.md) §6.

## Posts without a Reel

The Reel panel and the Reel caption appear only when the calls JSON has a `reel_length`. Leave `reel_length` out when no Reel was rendered: on carousel-only `/dead-air-carousel` runs. Update posts have a Reel, four slides, a caption and alt text like any other post.

## Known quirk

An ad-hoc story has `record_id: null`, so the stories table prints "None" in the record column. This is cosmetic.
