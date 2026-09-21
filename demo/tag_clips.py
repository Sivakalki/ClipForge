"""One-time offline tagging script for the demo clip library.

Writes one JSON sidecar per clip into /demo/tags/, matching the exact
schema documented in CLAUDE.md ("Tag sidecar schema"). This demo hand-labels
tags instead of running a real NPU model -- the goal is proving the schema
and the downstream matcher/render pipeline work end-to-end, not proving
live inference (that's the actual hackathon phone-app build, out of scope
here per demo_build_steps.md).

Run once: python demo/tag_clips.py
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from subprocess import run, DEVNULL

DEMO_DIR = Path(__file__).parent
CLIPS_DIR = DEMO_DIR / "clips"
TAGS_DIR = DEMO_DIR / "tags"

# Hand-assigned tags per clip: (t_start, t_end, label, confidence)
HAND_LABELS = {
    "order_placing.mp4": [
        (0.0, 2.76, "Order Placed", 0.94),
    ],
    "order_received.mp4": [
        (0.0, 2.64, "Package Arrival", 0.91),
    ],
    "unboxing.mp4": [
        (0.0, 2.0, "Unboxing", 0.93),
        (2.0, 4.12, "Product Reveal", 0.90),
    ],
}


def probe_duration(clip_path: Path) -> float:
    """Best-effort duration probe via ffprobe; falls back to the tag span."""
    try:
        result = run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(clip_path)],
            capture_output=True, text=True, timeout=10,
        )
        return round(float(result.stdout.strip()), 2)
    except Exception:
        return 0.0


def tag_clip(clip_path: Path) -> dict:
    labels = HAND_LABELS.get(clip_path.name, [])
    duration = probe_duration(clip_path) or (labels[-1][1] if labels else 0.0)
    return {
        "clip_id": clip_path.stem,
        "file": f"clips/{clip_path.name}",
        "duration_s": duration,
        "tags": [
            {"t_start": t0, "t_end": t1, "label": label, "confidence": conf}
            for t0, t1, label, conf in labels
        ],
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
    }


def main():
    TAGS_DIR.mkdir(exist_ok=True)
    clips = sorted(CLIPS_DIR.glob("*.mp4"))
    if not clips:
        print(f"No clips found in {CLIPS_DIR}")
        return
    for clip_path in clips:
        sidecar = tag_clip(clip_path)
        out_path = TAGS_DIR / f"{clip_path.stem}.json"
        out_path.write_text(json.dumps(sidecar, indent=2) + "\n")
        print(f"tagged {clip_path.name} -> {out_path.name} ({len(sidecar['tags'])} tags)")


if __name__ == "__main__":
    main()
