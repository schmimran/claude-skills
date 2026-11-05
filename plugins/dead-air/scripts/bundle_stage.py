"""Stage one post's hand-off bundle, and enforce its naming convention (0.4.0):
python3 bundle_stage.py <post.json> <out_dir> <calls.json> <folder>   stage <out_dir>/<folder>/, print its files
python3 bundle_stage.py --check <dir>                                 check a staged folder against the convention

<folder> is <YYYY-MM-DD>_<format><NN>, e.g. 2026-11-05_bundle01. The staged folder holds exactly:
  slide_01.png ... slide_NN.png   contiguous from 01, posting order; NN = the post's `alt` count
  video.mp4                       only when the calls JSON has `reel_length` (a Reel was rendered)
  caption_carousel.txt            the post's `caption`, UTF-8, plus one trailing newline
  caption_video.txt               the post's `reel_caption` (only with a Reel), same rules
The media is copied byte for byte from the render folder (`schmimknews-<date>-<format>-NN.png`, `-reel.mp4`).

Why a folder and not a zip: a published artifact can't serve a .zip, and a viewer blocks downloads a page starts
itself. So the folder's files are published under their convention names, and the review page zips them in the
viewer's browser (JSZip) and hands the zip over through the `downloads` capability. The names here are the zip's.

On success the script prints one `<folder>/<file>` path per line (relative to <out_dir>: the paths to publish) and
records `bundle` (the folder) and `bundle_files` (the file names) in the calls JSON; the review page shows the
bundle button only when both are there. Any deviation exits 1, stages nothing, removes a stale staged folder and
removes `bundle`/`bundle_files` from the calls, so a failed build can't leave a link to files that don't exist.
Stdlib only. Run as python3 -B."""
import json, os, re, shutil, sys
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
    """`<folder>/<file>` names -> problems. One root folder, exactly the allowed files, slides contiguous from 01,
    captions present, video and its caption together."""
    files = [n for n in names if not n.endswith("/")]
    roots = {n.split("/", 1)[0] for n in files}
    if len(roots) != 1: return [f"the bundle needs exactly one root folder, found {sorted(roots) or 'none'}"]
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

def stage(post, out, calls, folder):
    """Return (file names in posting order, problems). Stages nothing unless there are no problems."""
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
    dest, tmp = out / folder, out / f"{folder}.part"
    shutil.rmtree(tmp, ignore_errors=True); tmp.mkdir()
    for name, b in data.items(): (tmp / name).write_bytes(b)
    back = [f"{k} differs from its source after staging" for k, b in data.items() if (tmp / k).read_bytes() != b]   # read it back before it counts
    back += [f"{tmp.name}: {e}" for e in layout_errors([f"{folder}/{p.name}" for p in tmp.iterdir()])]
    if back: shutil.rmtree(tmp, ignore_errors=True); return None, back
    shutil.rmtree(dest, ignore_errors=True); tmp.rename(dest)
    return list(data), []

def write_calls(path, calls):
    tmp = Path(str(path) + ".tmp")
    tmp.write_text(json.dumps(calls, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"); os.replace(tmp, path)

def main():
    a = sys.argv[1:]
    if a[:1] == ["--check"] and len(a) == 2:
        d = Path(a[1])
        if not d.is_dir(): sys.exit(f"bundle_stage: {a[1]} is not a folder")
        errs = layout_errors([f"{d.name}/{p.relative_to(d).as_posix()}" for p in sorted(d.rglob("*")) if p.is_file()])
        print("\n".join(errs) if errs else "ok"); sys.exit(1 if errs else 0)
    if len(a) != 4: sys.exit("usage: bundle_stage.py <post.json> <out_dir> <calls.json> <folder> | --check <dir>")
    post, calls, out, folder = json.load(open(a[0])), json.load(open(a[2])), Path(a[1]), a[3]
    names, errs = stage(post, out, calls, folder)
    if errs:
        if not folder_errors(folder):   # a validated name can't point outside <out_dir>
            shutil.rmtree(out / folder, ignore_errors=True); shutil.rmtree(out / f"{folder}.part", ignore_errors=True)
        if "bundle" in calls or "bundle_files" in calls:
            calls.pop("bundle", None); calls.pop("bundle_files", None); write_calls(a[2], calls)
        sys.exit("bundle_stage: nothing staged.\n  " + "\n  ".join(errs))
    calls["bundle"], calls["bundle_files"] = folder, names; write_calls(a[2], calls)
    print("\n".join(f"{folder}/{n}" for n in names))

if __name__ == "__main__":
    main()
