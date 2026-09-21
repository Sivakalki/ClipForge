"""Prepares the raw uploaded footage in demo/clips_raw/ into the final
per-beat clips in demo/clips/ that the rest of the pipeline (tag_clips.py,
matcher.py, render.py) consumes.

Kept as a separate, re-runnable step from render.py: this is one-time
editorial work (pick the best moment in each source video, normalize
dimensions, add energy) on raw footage, not something the render step
should redo on every run.

For each clip: trim to the chosen window, crop+scale any mismatched
dimensions to the shared portrait frame (matches order_placing.mp4 and
unboxing.mp4, which were shot vertically), and speed up slightly so the
cut feels snappier against the background music.
"""

import subprocess
from pathlib import Path

RAW_DIR = Path(__file__).parent / "clips_raw"
OUT_DIR = Path(__file__).parent / "clips"

TARGET_SIZE = (1080, 1920)  # portrait, matches the two vertically-shot clips

# (source file, trim start, trim duration, speed multiplier, needs_crop)
CLIPS = [
    ("order_placing.mp4", 0.0, 3.0, 1.1, False),
    ("order_received.mp4", 8.0, 3.0, 1.15, True),  # 4096x2160 landscape -> crop to portrait
    ("unboxing.mp4", 3.0, 4.53, 1.1, False),
]


def prepare_clip(src: Path, start: float, duration: float, speed: float, needs_crop: bool, dst: Path):
    w, h = TARGET_SIZE
    filters = []
    if needs_crop:
        # center-crop the source to the target aspect ratio before scaling
        filters.append(f"crop=ih*{w}/{h}:ih")
    filters.append(f"scale={w}:{h}")
    filters.append(f"setpts=PTS/{speed}")
    vf = ",".join(filters)

    cmd = [
        "ffmpeg", "-y",
        # -ss/-t as INPUT options: reads exactly `duration` seconds of source
        # starting at `start`, before the speed filter compresses it further.
        # (placing -t after -i would cap *output* duration instead, pulling
        # in extra unwanted source footage to fill the sped-up gap.)
        "-ss", str(start), "-t", str(duration), "-i", str(src),
        "-vf", vf,
        "-an",  # drop each clip's own audio; render.py overlays one music track
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-loglevel", "error",
        str(dst),
    ]
    subprocess.run(cmd, check=True)


def main():
    OUT_DIR.mkdir(exist_ok=True)
    for name, start, duration, speed, needs_crop in CLIPS:
        src = RAW_DIR / name
        dst = OUT_DIR / name
        prepare_clip(src, start, duration, speed, needs_crop, dst)
        print(f"prepared {name}: trim {start}-{start + duration}s, speed {speed}x -> {dst}")


if __name__ == "__main__":
    main()
