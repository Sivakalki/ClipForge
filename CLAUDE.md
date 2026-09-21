# CLAUDE.md

Guidance for Claude Code (or any AI coding assistant) working in this repo.

## Project

**ClipForge** — an NPU-native rough-cut engine built for the iQOO Hackathon 2026 (Hyderabad City Battle, Team Kaizen, track: Productivity).

Shoot clips on the iQOO 15; a local NPU model tags each clip in real time as it's recorded. Sync the tagged clip library to a laptop; a matcher aligns a user-supplied script to the best-tagged clips; FFmpeg renders a rough-cut video with a trending audio track. No cloud calls anywhere in the pipeline.

## Build structure

The hackathon splits build time into two phases — code accordingly:

- **Red Light (phone only, ~55% of build time):** everything must run standalone on the iQOO 15, no laptop involved. This is the `/phone-app` component.
- **Green Light (phone + laptop, ~45%):** the laptop only becomes useful once it has received the phone's tagged clip library. This is the `/laptop-app` component.

Do not build features that blur this split (e.g. laptop-side logic that's needed during Red Light, or phone-side logic that depends on the laptop being present).

## Repo layout

```
/phone-app       # Android — capture UI + on-device NPU tagging
/laptop-app      # Python — sync receiver, script matcher, FFmpeg renderer
/shared          # JSON schema for the tag sidecar file, shared by both sides
/assets          # sample clips, sample scripts for local testing
```

## Tech stack

| Layer | Tool | Notes |
| --- | --- | --- |
| Capture | CameraX (Kotlin, Android) | Custom capture screen, not the stock camera app |
| On-device tagging | YOLOv8-Nano or MobileNetV3, `.tflite` / ONNX Mobile | Pre-trained + quantized — do not train during the hackathon |
| NPU acceleration | Android NNAPI delegate | Must run on the NPU, not CPU/GPU fallback |
| Local tag storage | Plain JSON sidecar per clip | Schema below |
| Phone → laptop sync | Local file transfer (Office Kit at the event; a folder-watch script or ADB works fine for local dev) | Keep this swappable — don't hardcode Office Kit APIs into core logic |
| Laptop app | Python 3.11+ | |
| Script-to-clip matching | Rule-based tag/keyword matcher | Ship this first; only add an embedding-based matcher (e.g. `sentence-transformers`, MiniLM) if time remains |
| Video assembly | FFmpeg via subprocess, or `moviepy` | |

## Tag sidecar schema (`/shared/tag_schema.json`)

```json
{
  "clip_id": "string",
  "file": "relative/path/to/clip.mp4",
  "duration_s": 3.2,
  "tags": [
    { "t_start": 0.0, "t_end": 1.5, "label": "Product Close-up", "confidence": 0.92 },
    { "t_start": 1.5, "t_end": 3.2, "label": "Bright Lighting", "confidence": 0.88 }
  ],
  "created_at": "ISO-8601 timestamp"
}
```

Both `/phone-app` and `/laptop-app` must read/write this exact shape — treat it as the contract between the two components.

## Build priority (MVP order)

Build and demo-check each step before starting the next; every step below should be independently demoable if time runs out.

1. Camera capture screen
2. On-device NPU tagging, writing the JSON sidecar
3. Phone → laptop sync
4. Rule-based script-to-clip matcher
5. FFmpeg auto-cut + audio overlay

## Explicitly out of scope for the MVP

Don't build these unless the priority list above is fully done with time to spare:

- Live trend-scraping from social platform APIs (gated/rate-limited — use a manually entered or curated script instead)
- Cross-attention or ML-based beat matching (the rule-based matcher is the target, not a stretch)
- Local LLM script generation (only as a stretch, via `llama.cpp` with a small quantized model — never a cloud LLM call)
- Multi-track audio, captions, color grading, or any other post-MVP polish

## Conventions

- Kotlin for `/phone-app`; standard Android Studio project layout.
- Python for `/laptop-app`; keep `matcher.py` and `renderer.py` as separate, independently testable modules — don't couple matching logic to the FFmpeg call.
- No network calls anywhere in `/phone-app`. If you're about to add one, stop — it breaks the "on-device" story the whole project is built around.
- Favor a working rough cut over a polished one. A simple product that runs end-to-end beats a complex one that doesn't.
