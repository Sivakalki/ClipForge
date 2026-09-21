# ClipForge demo

Offline, single-machine walkthrough of the ClipForge pipeline (see
`../CLAUDE.md` and `../demo_build_steps.md`). No camera, no NPU, no
phone/laptop sync — that's the real hackathon build, not this.

## Prerequisites

- Python 3.11+
- `ffmpeg` (and `ffprobe`) installed and on PATH

## Sample footage

`demo/clips_raw/*.mp4` are 3 user-supplied clips of one continuous story —
same person, same setting throughout:

1. `order_placing.mp4` — placing an order online (1080x1920 portrait)
2. `order_received.mp4` — the branded package arriving (4096x2160 landscape)
3. `unboxing.mp4` — opening the box and revealing the product (1080x1920 portrait)

`demo/prepare_clips.py` turns these into the final `demo/clips/*.mp4` used
by the rest of the pipeline: each is trimmed to its best moment, sped up
~10-15% for a snappier cut, and `order_received.mp4` — shot landscape — is
center-cropped to match the portrait frame of the other two. Re-run it if
you swap in different raw footage:

```bash
python3 demo/prepare_clips.py
```

## Audio track

`assets/trending_audio.mp3` is "Instrumental TikTok Trending Music" by
alex-morgan, via Pixabay (free, Pixabay Content License, no attribution
required — https://pixabay.com/music/instrumental-tiktok-trending-music-548616/).
`render.py` loops it to cover the full merged video length regardless of
clip count.

## Run (CLI)

```bash
python3 demo/tag_clips.py   # one-time: writes demo/tags/*.json
python3 demo/run_demo.py    # matches script -> clips, renders rough cut
```

Output: `demo/output/rough_cut.mp4`.

## Run (demo UI)

A single-page local UI for showing this live: type one prompt, hit
Generate, watch the real pipeline run and the rough cut play back.

```bash
python3 demo/webapp/server.py
```

The page also shows the 3 raw clips (`demo/clips_raw/`, served via
`/raw/<file>`) side by side with the generated output, so judges can compare
source footage against the result. The upload zone above them is disabled
by design — clicking or dropping onto it shows an inline notice ("this is a
demo build, no new videos can be added") instead of opening a file picker.
Generate always renders the fixed curated sequence; wiring arbitrary
uploaded video into the live pipeline was judged too fragile for a demo.

Then open http://localhost:8000/. The prompt you type becomes the on-screen
caption for the first beat ("Order Placed") — it's not a fake loading
animation, Generate actually re-runs `matcher.py` + `render.py` server-side.
