"""Minimal local demo server -- stdlib only, no framework, for the hackathon
demo UI. Serves the single-page app and, on Generate, actually re-runs the
real pipeline (matcher.py -> render.py) rather than faking the result.

Run: python3 demo/webapp/server.py
Then open http://localhost:8000/
"""

import json
import os
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

DEMO_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(DEMO_DIR))

from matcher import match  # noqa: E402
from render import render  # noqa: E402

WEBAPP_DIR = Path(__file__).resolve().parent
SCRIPT_PATH = DEMO_DIR / "script.json"
TAGS_DIR = DEMO_DIR / "tags"
CLIPS_DIR = DEMO_DIR / "clips"
RAW_DIR = DEMO_DIR / "clips_raw"
AUDIO_PATH = DEMO_DIR.parent / "assets" / "trending_audio.mp3"
OUTPUT_DIR = DEMO_DIR / "output"
OUTPUT_PATH = OUTPUT_DIR / "rough_cut.mp4"

# Hosting platforms (Render, Hugging Face Spaces, etc.) assign the port via
# $PORT; default to 8000 for local runs.
PORT = int(os.environ.get("PORT", 8000))


def generate_rough_cut() -> Path:
    """Runs the real pipeline: matches script beats to tagged clips, then
    renders the final cut. The UI's instruction textarea (merge/resize/
    music/subtitles) describes what this already does by default -- none
    of it is burned into the video; on-screen captions stay the curated
    per-beat action descriptions from script.json."""
    matches = match(str(SCRIPT_PATH), str(TAGS_DIR))
    script = json.loads(SCRIPT_PATH.read_text())
    caption_by_beat = {b["beat"]: b["text"] for b in script["beats"]}
    captions = [caption_by_beat.get(beat) for beat, _clip in matches]

    clip_order = [CLIPS_DIR / clip for _, clip in matches]
    missing = [c for c in clip_order if not c.exists()]
    if missing:
        raise FileNotFoundError(f"missing clip file(s): {missing}")

    return render(clip_order, AUDIO_PATH, OUTPUT_PATH, captions=captions)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

    def _send_json(self, status: int, payload: dict):
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, path: Path, content_type: str):
        if not path.exists():
            self.send_error(404, "Not found")
            return
        data = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/":
            self._send_file(WEBAPP_DIR / "index.html", "text/html")
        elif path.startswith("/output/"):
            name = path.removeprefix("/output/")
            self._send_file(OUTPUT_DIR / name, "video/mp4")
        elif path.startswith("/raw/"):
            # serves the original uploaded footage, unmodified, for side-by-side
            # comparison against the rendered cut -- never used as a write target
            name = path.removeprefix("/raw/")
            if "/" in name or Path(name).name != name:
                self.send_error(400, "Bad request")
                return
            self._send_file(RAW_DIR / name, "video/mp4")
        else:
            self.send_error(404, "Not found")

    def do_POST(self):
        path = urlparse(self.path).path
        if path != "/api/generate":
            self.send_error(404, "Not found")
            return

        length = int(self.headers.get("Content-Length", 0))
        try:
            body = json.loads(self.rfile.read(length) or b"{}")
            prompt = str(body.get("prompt", "")).strip()[:200]
        except json.JSONDecodeError:
            self._send_json(400, {"error": "invalid JSON body"})
            return

        print(f"[generate] instruction received:\n{prompt}\n")
        try:
            generate_rough_cut()
        except Exception as exc:  # noqa: BLE001 -- report any pipeline failure to the UI
            self._send_json(500, {"error": str(exc)})
            return

        cache_bust = int(time.time())
        self._send_json(200, {"video_url": f"/output/rough_cut.mp4?t={cache_bust}"})


def main():
    OUTPUT_DIR.mkdir(exist_ok=True)
    server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    print(f"ClipForge demo UI: http://localhost:{PORT}/")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
