"""Build one post's hand-off zip, and enforce its naming convention (0.4.0):
python3 bundle_zip.py <post.json> <out_dir> <calls.json> <folder>   build <out_dir>/<folder>.zip, print its path
python3 bundle_zip.py --check <file.zip>                            check an existing zip against the convention

<folder> is <YYYY-MM-DD>_<format><NN>, e.g. 2026-11-05_bundle01. The zip has that one root folder and nothing else but:
  slide_01.png ... slide_NN.png   contiguous from 01, posting order; NN = the post's `alt` count
  video.mp4                       only when the calls JSON has `reel_length` (a Reel was rendered)
  caption_carousel.txt            the post's `caption`, UTF-8, plus one trailing newline
  caption_video.txt               the post's `reel_caption` (only with a Reel), same rules
The media is copied from the render folder (`schmimknews-<date>-<format>-NN.png`, `-reel.mp4`); nothing is re-encoded.
Any deviation exits 1 and writes no zip. On success the script records `"bundle": "<folder>"` in the calls JSON (the
review page links the zip only when that field exists); on a refusal it removes any `bundle` already there, so a
failed build can never leave a link to a zip that doesn't exist. Stdlib only. Run as python3 -B."""
import json, os, re, sys, zipfile
from pathlib import Path

sys.dont_write_bytecode = True
from render import post_stem   # the one definition of the render file stem (stdlib-only at import; Playwright loads in main)

FORMATS = ("bundle", "weekly", "single", "deep", "update")
FOLDER = re.compile(r"([0-9]{4}-[0-9]{2}-[0-9]{2})_(" + "|".join(FORMATS) + r")([0-9]{2})")   # used with fullmatch
SLIDE = re.compile(r"slide_[0-9]{2}\.png")
FIXED = {"video.mp4", "caption_video.txt", "caption_carousel.txt"}

def folder_errors(folder):
    m = FOLDER.fullmatch(folder) if isinstance(folder, str) else None
    if not m: return [f"folder {folder!r} must read <YYYY-MM-DD>_<{'|'.join(FORMATS)}><NN>, e.g. 2026-11-05_bundle01"]
    return ["folder counter must be 01 or higher"] if int(m.group(3)) == 0 else []

def layout_errors(names):
    """Zip entry names -> problems. One root folder, exactly the allowed files, slides contiguous from 01,
    captions present, video and its caption together."""
    files = [n for n in names if not n.endswith("/")]
    roots = {n.split("/", 1)[0] for n in files}
    if len(roots) != 1: return [f"the zip needs exactly one root folder, found {sorted(roots) or 'none'}"]
    root = roots.pop()
    errs, leaf = folder_errors(root), set()
    for n in files:
        parts = n.split("/")
        if len(parts) != 2: errs.append(f"'{n}' is not directly inside {root}/")
        else: leaf.add(parts[1])
    slides = sorted(k for k in leaf if SLIDE.fullmatch(k))
    errs += [f"'{k}' is not an allowed file name" for k in sorted(leaf) if k not in FIXED and not SLIDE.fullmatch(k)]
    if not slides: errs.append("no slide_NN.png files")
    elif slides != [f"slide_{i:02d}.png" for i in range(1, len(slides) + 1)]:
        errs.append(f"slides must be numbered 01..{len(slides):02d} with no gaps, got {slides}")
    if "caption_carousel.txt" not in leaf: errs.append("caption_carousel.txt is missing")
    if ("video.mp4" in leaf) != ("caption_video.txt" in leaf): errs.append("video.mp4 and caption_video.txt go together; one is missing")
    if len(set(names)) != len(names): errs.append("duplicate entries")
    return errs

def build(post, out, calls, folder):
    """Return (zip path, problems). Writes nothing unless there are no problems."""
    errs = folder_errors(folder)
    if m := FOLDER.fullmatch(folder) if isinstance(folder, str) else None:
        if m.group(1) != post["date"]: errs.append(f"folder date {m.group(1)} is not the post date {post['date']}")
        if m.group(2) != post["format"]: errs.append(f"folder format {m.group(2)} is not the post format {post['format']}")
    stem, n = post_stem(post), len(post.get("alt") or [])
    srcs = {f"slide_{i:02d}.png": out / f"{stem}-{i:02d}.png" for i in range(1, n + 1)}
    if n == 0: errs.append("post has no `alt` strings, so no slide count")
    extra = len(list(out.glob(f"{stem}-[0-9][0-9].png"))) - n   # a missing slide is reported per file below
    if extra > 0: errs.append(f"{n + extra} slide PNGs in {out}, the post has {n} alt strings")
    caps = {"caption_carousel.txt": post.get("caption")}
    if calls.get("reel_length"):
        srcs["video.mp4"] = out / f"{stem}-reel.mp4"; caps["caption_video.txt"] = post.get("reel_caption")
    errs += [f"{k} source missing: {p}" for k, p in srcs.items() if not p.is_file()]
    errs += [f"{k.replace('.txt', '')}: the post has no text for it" for k, v in caps.items() if not (isinstance(v, str) and v.strip())]
    if errs: return None, errs
    data = {k: p.read_bytes() for k, p in srcs.items()}
    data.update({k: v.rstrip("\n").encode("utf-8") + b"\n" for k, v in caps.items()})
    when = tuple(int(x) for x in post["date"].split("-")) + (0, 0, 0)   # fixed stamp: same inputs, same bytes
    dest, tmp = out / f"{folder}.zip", out / f"{folder}.zip.part"
    with zipfile.ZipFile(tmp, "w") as z:
        for name, b in data.items():
            z.writestr(zipfile.ZipInfo(f"{folder}/{name}", when), b, zipfile.ZIP_DEFLATED if name.endswith(".txt") else zipfile.ZIP_STORED)
    with zipfile.ZipFile(tmp) as z:   # read it back before it counts: entries, CRCs, every byte
        bad = z.testzip()
        back = [f"zip CRC check failed at {bad}"] if bad else []
        if sorted(z.namelist()) != sorted(f"{folder}/{k}" for k in data): back.append(f"zip lists {sorted(z.namelist())}, wanted {sorted(data)}")
        else: back += [f"{k} differs from its source after zipping" for k, b in data.items() if z.read(f"{folder}/{k}") != b]
    if back: tmp.unlink(); return None, back
    tmp.replace(dest)
    return dest, []

def write_calls(path, calls):
    tmp = Path(str(path) + ".tmp")
    tmp.write_text(json.dumps(calls, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"); os.replace(tmp, path)

def main():
    a = sys.argv[1:]
    if a[:1] == ["--check"] and len(a) == 2:
        try: errs = layout_errors(zipfile.ZipFile(a[1]).namelist())
        except (OSError, zipfile.BadZipFile) as e: sys.exit(f"bundle_zip: can't read {a[1]} as a zip: {e}")
        print("\n".join(errs) if errs else "ok"); sys.exit(1 if errs else 0)
    if len(a) != 4: sys.exit("usage: bundle_zip.py <post.json> <out_dir> <calls.json> <folder> | --check <file.zip>")
    post, calls = json.load(open(a[0])), json.load(open(a[2]))
    dest, errs = build(post, Path(a[1]), calls, a[3])
    if errs:
        if "bundle" in calls: del calls["bundle"]; write_calls(a[2], calls)   # never leave a link to a zip that wasn't built
        sys.exit("bundle_zip: no zip written.\n  " + "\n  ".join(errs))
    calls["bundle"] = a[3]; write_calls(a[2], calls)
    print(dest)

if __name__ == "__main__":
    main()
