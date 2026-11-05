# Review page

SPEC §5.3 and §10.1. Every post gets its own dated review page: a **new** claude.ai artifact per post. Never republish over an earlier post's page.

## What it shows

`review_page.py` builds the page. In order, it shows:

1. A header and facts strip: the calls JSON's `facts`.
2. **The Reel first:** the MP4, with the cover as its poster, plus its headline.
3. **The carousel strip:** every slide in posting order, each with its label and alt text.
4. **Both captions,** each with a Copy button.
5. **The stories in the post:** title or headline, record ID, dateline, count or stat, confidence.
6. **The calls:** every judgment from the calls JSON.

It is a single dark page in the feed's own look. It loads Google Fonts for its own type; that request is allowed on a published artifact, unlike in the render workspace.

## Building and publishing

```
python3 review_page.py <post.json> <out_dir> <calls.json> [--title …] [--h1 …] [--name …]
```

- Run it with `<out_dir>` set to the render folder, so the HTML and the media files sit side by side. It prints the path of the HTML it wrote.
- **Dashboard posts:** no flags. The title is "Dead Air <Mon D>", the h1 is "Dead Air · <Mon D YYYY>", and the file is `dead-air-<date>.html`.
- **Standalone deep posts (`/dead-air-reel`):** `--title "Dead Air: <Slug>"`, `--h1 "Dead Air · <The subject>"`, `--name dead-air-<slug>`.
- Every post renders into its own `dead-air/out/<name>/` folder, so a second post on the same day (the second Reel's deep post, or a `-v2` re-cut) never overwrites the first one's files.

**Publish** with the Artifact tool:
- Load the `artifact-design` skill before the first publish of a session.
- `file_path` is the HTML. `files` maps every carousel PNG, the `-reel.mp4` and the `-reel-cover.png` to themselves by filename; the page references them by bare filename. Don't publish `checks.json` or `.reel-frames/`.
- Each post is a new artifact with a new path; don't pass `url`.
- Keep the returned link: it goes in the post's `.md`, the IG Posts row and the report.

If the Artifact tool can't publish, follow [render-guide.md](render-guide.md) §6.

## Known quirk

An ad-hoc story has `record_id: null`, so the stories table prints "None" in the record column. This is cosmetic; the script was ported as-is.
