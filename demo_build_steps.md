# DEMO_BUILD_STEPS.md

Task list for building the lightweight ClipForge demo — a stripped-down, offline version of the pipeline meant to explain the product, not the full hackathon build. Read this alongside `CLAUDE.md` (project overview, tech stack, tag schema) before starting; this file only covers what's different for the demo.

**Scope note for the agent:** this demo intentionally skips live camera capture, real-time NPU inference, and the phone/laptop sync step described in `CLAUDE.md`. Everything here runs offline on one machine, from a folder of sample clips to a finished rendered video. Do not build the Android app, the sync mechanism, or real-time tagging for this task — that's separate, later work for the actual hackathon build.

## Prerequisites

- Python 3.11+
- FFmpeg installed and on PATH
- A folder of 4–5 short sample video clips (from a phone gallery or free stock footage), placed in `/assets/demo_clips/`

## Steps

### 1. Set up the demo folder structure

Create `/demo/` at the repo root with:
```
/demo
  /clips        # copy or symlink the sample clips here
  /tags         # one JSON file per clip, written in step 2
  script.json   # the hardcoded script, written in step 3
  matcher.py    # step 3
  render.py     # step 4
  run_demo.py   # step 5, ties it all together
```

### 2. Tag each clip (offline, one-time script)

Write `/demo/tag_clips.py`:
- For each file in `/demo/clips/`, produce a JSON tag file in `/demo/tags/` using the exact schema in `CLAUDE.md` under "Tag sidecar schema."
- It's fine to hand-assign the `tags` array for this demo instead of running a real model — the goal is proving the schema and downstream pipeline work, not proving live inference. If a pre-trained lightweight classifier is easy to drop in (e.g. a general-purpose image classifier run on a few sampled frames per clip), use it; otherwise hand-label plausibly.
- Run this once per clip and commit the resulting JSON files — they don't need to regenerate on every demo run.

### 3. Hardcode the script and matcher

Write `/demo/script.json`:
```json
{
  "beats": [
    { "beat": "Hook", "text": "You won't believe this reveal." },
    { "beat": "Body", "text": "Show the product up close, then the full setup." },
    { "beat": "CTA", "text": "Tag a friend who needs this." }
  ]
}
```

Write `/demo/matcher.py`:
- A single function `match(script_path, tags_dir) -> list[(beat, clip_filename)]`.
- For the demo, a hardcoded mapping (dict from beat name to clip filename) is acceptable — this proves the concept without needing real matching logic. If time allows, do a simple keyword match between the beat text and each clip's tags instead.

### 4. Render the rough cut

Write `/demo/render.py`:
- Takes the matcher's output (ordered list of clip filenames) and one audio file (any royalty-free trending-style track dropped into `/assets/`).
- Uses a single FFmpeg command (via `subprocess`) to concatenate the matched clips in order and overlay the audio track.
- Outputs to `/demo/output/rough_cut.mp4`.
- Keep this to one function, `render(clip_order, audio_path, output_path)` — no need for a class or config system.

### 5. Tie it together

Write `/demo/run_demo.py`:
- Runs matcher.py against script.json and the tags in /demo/tags/, then passes the result to render.py.
- Prints each step's output to the terminal as it happens (matched beats, clip order, then "Rendering..." then the final output path) — this terminal output is what gets screen-recorded for the explainer video, so make it readable, not just a silent success/failure.
- Single command to run the whole demo: `python demo/run_demo.py`.

### 6. Record and narrate

Not a coding task — screen-record `run_demo.py`'s terminal output followed by the finished video playing, then narrate over it using the walkthrough script from the "ClipForge — Walkthrough Video Script" doc, adjusted to describe what's actually on screen (terminal + rendered video, not live phone capture).

## Definition of done

- `python demo/run_demo.py` runs start to finish with no manual steps in between.
- `/demo/output/rough_cut.mp4` plays and shows the matched clips in the right order with audio.
- Nothing in `/demo/` touches the Android app, real NPU inference, or the phone/laptop sync — those stay out of scope until the actual hackathon build.
