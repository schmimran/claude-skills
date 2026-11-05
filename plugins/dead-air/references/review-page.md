# Review page

SPEC §5.3 and §10.1, with addendum v2.1 §A and v2.2 §G. Every day's post gets its own dated review page: a **new** claude.ai artifact per post. Never republish over an earlier post's page. **Update companions are the exception:** they go on the day's page, not a page of their own.

## What it shows

`review_page.py` builds the page. In order, it shows:

1. A header and facts strip: the calls JSON's `facts`.
2. **The Reel first:** the MP4, with the cover as its poster, plus its headline, a **Download video** button and a **Download cover** link.
3. **The carousel strip:** every slide in posting order, each with its label, its own download link and its alt text, then a **Download bundle zip** link (when the post has one) and a **Download all slides** button.
4. **Both captions,** each with a Copy button.
5. **The stories in the post:** title or headline, record ID, dateline, count or stat, confidence.
6. **The calls:** every judgment from the calls JSON.
7. **Each Update companion** (if any), under an amber rule: its own facts strip, then 2–6 for the companion, with its own Copy buttons.

## Downloads (addendum v2.2 §G)

Imran, Nov 5: grabbing the video from a phone should be one tap.

- **Download video**, under every Reel: `<a href="<stem>-reel.mp4" download="<stem>-reel.mp4">`, full-width, at least 48px tall.
- **Download cover**, under it: the Reel cover, `<stem>-reel-cover.png`, same `download` attribute.
- **Download bundle zip** (0.4.0), above "Download all slides" under every carousel strip, when the post's calls JSON has `bundle` (recorded by `bundle_zip.py` after a verified build): `<a href="<bundle>.zip" download="<bundle>.zip">`, full-width, at least 48px tall. It is the hand-off: the slides, the Reel and both captions in the fixed layout of [render-guide.md](render-guide.md) §7, built on the machine by `bundle_zip.py`, so it works as a plain file download. Without `bundle` the button is left out.
- **Download all slides**, under every carousel strip: zips that post's PNGs in the browser with JSZip 3.10.1 from cdnjs (pinned) and saves `<stem>-slides.zip`. If JSZip didn't load or a fetch fails, the button says to use the slide links instead.
- **Download slide NN**, under each slide: for phones that can't open zips.
- Every link carries the `download` attribute, so iOS Safari saves the file instead of opening it.

Update companions get the same set, in their own section. A carousel-only page has no Reel, so no video or cover link.

## Look

It is a single dark page in the feed's own look. It loads Google Fonts for its own type; that request is allowed on a published artifact, unlike in the render workspace.

## Building and publishing

```
python3 -B <DA_ROOT>/scripts/review_page.py <post.json> <out_dir> <calls.json> [--companion <update.json> <update-calls.json>]... [--title …] [--h1 …] [--name …]
```

- Run it with `<out_dir>` set to the render folder, so the HTML and the media files sit side by side. It prints the path of the HTML it wrote.
- **Dashboard posts:** no flags. The title is "Dead Air <Mon D>", the h1 is "Dead Air · <Mon D YYYY>", and the file is `dead-air-<date>.html`.
- **Update companions:** pass each with `--companion`, oldest pickup first, at most two. The script refuses a companion dated differently from the day's post or using its ask.
- **Standalone deep posts (`/dead-air-reel`):** `--title "Dead Air: <Slug>"`, `--h1 "Dead Air · <The subject>"`, `--name dead-air-<slug>`.
- Every post renders into its own `DA_WS/out/<name>/` folder, so a second post on the same day (the second Reel's deep post, or a `-v2` re-cut) never overwrites the first one's files.

**Publish** with the Artifact tool:
- Load the `artifact-design` skill before the first publish of a session.
- `file_path` is the HTML. `files` maps every carousel PNG, the `-reel.mp4` and the `-reel-cover.png` to themselves by filename; the page references them by bare filename. It also maps the post's `<bundle>.zip` to itself, passing `contentType: "application/zip"` explicitly (the tool infers types only for common extensions, and publishing a zip has not been verified: if the publish refuses it, say so under Open calls). With companions, `files` also maps each companion's PNGs, MP4, cover and `<bundle>.zip` (same contentType) from its own `DA_WS/out/<date>-update-<slug>/` folder; the slug in their names keeps the media apart, and each zip's folder name (`update01`, `update02`) keeps the zips apart. Don't publish `checks.json`, `.reel-frames/` or a leftover `*.zip.part`. Run `bundle_zip.py` before the page is built ([render-guide.md](render-guide.md) §7).
- Each post is a new artifact with a new path; don't pass `url`.
- Keep the returned link: it goes in the post's `.md`, the IG Posts row and the report. A companion's `.md` and IG Posts row carry the same link.

If the Artifact tool can't publish, follow [render-guide.md](render-guide.md) §6.

## Posts without a Reel

The Reel panel and the Reel caption appear only when the calls JSON has a `reel_length`. Leave `reel_length` out when no Reel was rendered: on carousel-only `/dead-air-carousel` runs. Update posts have a Reel, four slides, a caption and alt text like any other post.

## Known quirk

An ad-hoc story has `record_id: null`, so the stories table prints "None" in the record column. This is cosmetic.
