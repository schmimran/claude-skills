#!/usr/bin/env python3
"""Real-browser check of the review page's download wiring (0.4.0). Run by check_fixtures.py with a Python that has Playwright:

  python3 -B check_page_downloads.py <flat dir> <page.html> <bundle folder>

<flat dir> holds the page and every file it references side by side, as a published artifact does (the render's PNGs
and MP4, and the staged <bundle folder>/). It is served over http://127.0.0.1, the page's own JavaScript runs in
Chromium, and `window.claude` is stubbed the way the claude.ai viewer provides it. Three scenarios:
  cap      the `downloads` capability is present: the bundle zip, "Download video" and "Download all slides" must reach
           downloads.save() with the right filename and the right bytes (the stub hashes what it receives)
  decline  the viewer says no: nothing is saved and the button comes back, no error shown
  nocap    no capability (a plain browser): the old link/blob download is the fallback, and the zip it produces is real
Prints one JSON object. Needs network for JSZip from cdnjs, exactly as the page does. Stdlib + Playwright."""
import functools, hashlib, http.server, json, socketserver, sys, tempfile, threading, zipfile
from pathlib import Path
from playwright.sync_api import sync_playwright

root, page_name, folder = Path(sys.argv[1]).resolve(), sys.argv[2], sys.argv[3]

class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass

srv = socketserver.TCPServer(("127.0.0.1", 0), functools.partial(Quiet, directory=str(root)))
threading.Thread(target=srv.serve_forever, daemon=True).start()
URL = f"http://127.0.0.1:{srv.server_address[1]}/{page_name}"

STUB = """
window.__saves = [];
window.claude = {use: async n => n === 'downloads' ? {save: async req => {
  if (%DECLINE%) throw {code: 'declined', message: 'no'};
  const sha = async b => [...new Uint8Array(await crypto.subtle.digest('SHA-256', b))].map(x => x.toString(16).padStart(2, '0')).join('');
  const buf = await req.data.arrayBuffer(); let entries = null;
  if (req.filename.endsWith('.zip')) { const z = await JSZip.loadAsync(buf); entries = {};
    for (const n of Object.keys(z.files)) if (!z.files[n].dir) entries[n] = await sha(await z.files[n].async('arraybuffer')); }
  window.__saves.push({filename: req.filename, size: buf.byteLength, sha: await sha(buf), entries});
  return {status: 'saved'}; }} : null};
"""

def open_page(browser, stub=None):
    ctx = browser.new_context(accept_downloads=True)
    if stub: ctx.add_init_script(stub)
    page = ctx.new_page(); page.goto(URL)
    page.wait_for_function("typeof JSZip !== 'undefined'", timeout=30000)   # the cdnjs script, as in production
    return page

out = {}
try:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        # cap: the capability is there
        page = open_page(browser, STUB.replace("%DECLINE%", "false"))
        page.wait_for_function("DL !== null", timeout=10000)
        page.click("button.dl-bundle"); page.wait_for_function("window.__saves.length >= 1", timeout=60000)
        page.click("a:has-text('Download video')"); page.wait_for_function("window.__saves.length >= 2", timeout=30000)
        page.click("button:has-text('Download all slides')"); page.wait_for_function("window.__saves.length >= 3", timeout=60000)
        out["cap"] = {"saves": page.evaluate("window.__saves"), "bundle_label": page.inner_text("button.dl-bundle")}
        # decline: the viewer says no
        page = open_page(browser, STUB.replace("%DECLINE%", "true"))
        page.wait_for_function("DL !== null", timeout=10000)
        label = page.inner_text("button.dl-bundle")
        page.click("button.dl-bundle")
        page.wait_for_function("!document.querySelector('button.dl-bundle').disabled", timeout=30000)
        out["decline"] = {"saves": page.evaluate("window.__saves"), "label_before": label, "label_after": page.inner_text("button.dl-bundle")}
        # nocap: no window.claude at all
        page = open_page(browser)
        with page.expect_download(timeout=30000) as dv: page.click("a:has-text('Download video')")
        video_name = dv.value.suggested_filename
        with page.expect_download(timeout=60000) as dz: page.click("button.dl-bundle")
        tmp = Path(tempfile.mkdtemp()) / "bundle.zip"; dz.value.save_as(str(tmp))
        z = zipfile.ZipFile(tmp)
        out["nocap"] = {"video_name": video_name, "zip_name": dz.value.suggested_filename, "names": z.namelist(), "testzip": z.testzip()}
        browser.close()
except Exception as e:   # reported, never raised: the caller records the failure with this text
    out["error"] = f"{type(e).__name__}: {str(e)[:400]}"
print(json.dumps(out))
