"""FFmpeg rough-cut renderer (demo version).

Kept independent of matcher.py per CLAUDE.md conventions -- this module only
knows how to concatenate an ordered list of clips and overlay one audio
track; it has no idea how that order was decided.

Source clips can be mixed resolution/aspect-ratio/fps (e.g. real stock
footage: 1080p landscape, 4K, vertical), so each clip is:
  - trimmed to CLIP_DURATION seconds (a snappy rough cut, not raw dumps)
  - scaled+cropped to fill a common 16:9 frame (no letterboxing)
  - optionally captioned with its script beat's text
before the concat filter -- ffmpeg's concat *demuxer* would otherwise
misinterpret mismatched timestamps and produce a corrupt duration.

The audio track is looped so it always covers the full merged video, no
matter how many clips are concatenated.
"""

import subprocess
import tempfile
from pathlib import Path

TARGET_SIZE = (1080, 1920)  # portrait, matches prepare_clips.py's output
TARGET_FPS = 25
CLIP_DURATION = 5.0  # cap per clip; source clips here are already pre-trimmed shorter
FONT_SIZE = 56


def _escape_drawtext_path(path: str) -> str:
    # ffmpeg filter syntax treats ':' and '\' specially even inside textfile=.
    return path.replace("\\", "\\\\").replace(":", "\\:")


def render(
    clip_order: list[Path],
    audio_path: Path,
    output_path: Path,
    captions: list[str] | None = None,
) -> Path:
    """Concatenate clip_order in sequence (trimmed + cropped to a common
    frame), burn in per-clip captions if given, and overlay audio_path
    (looped to cover the full length). Writes to output_path."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    w, h = TARGET_SIZE
    n = len(clip_order)
    captions = captions or [None] * n

    inputs = []
    for clip in clip_order:
        inputs += ["-i", str(clip)]
    audio_index = n
    inputs += ["-stream_loop", "-1", "-i", str(audio_path)]

    caption_files = []
    per_clip_filters = []
    labels = []
    try:
        for i in range(n):
            label = f"v{i}"
            chain = (
                f"[{i}:v]trim=duration={CLIP_DURATION},setpts=PTS-STARTPTS,"
                f"scale={w}:{h}:force_original_aspect_ratio=increase,"
                f"crop={w}:{h},setsar=1,fps={TARGET_FPS}"
            )
            if captions[i]:
                cap_file = tempfile.NamedTemporaryFile(
                    "w", suffix=".txt", delete=False
                )
                cap_file.write(captions[i])
                cap_file.close()
                caption_files.append(Path(cap_file.name))
                textfile = _escape_drawtext_path(cap_file.name)
                chain += (
                    f",drawtext=textfile='{textfile}':fontcolor=white:fontsize={FONT_SIZE}:"
                    f"box=1:boxcolor=black@0.5:boxborderw=16:x=(w-text_w)/2:y=h-th-40"
                )
            chain += f"[{label}]"
            per_clip_filters.append(chain)
            labels.append(f"[{label}]")

        concat_filter = f"{''.join(labels)}concat=n={n}:v=1:a=0[outv]"
        filter_complex = ";".join(per_clip_filters + [concat_filter])

        cmd = [
            "ffmpeg", "-y",
            *inputs,
            "-filter_complex", filter_complex,
            "-map", "[outv]", "-map", f"{audio_index}:a",
            "-filter:a", "volume=1.3",  # +~2.3dB; source peaks at -3.5dB so this stays clear of clipping
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-shortest",
            "-loglevel", "error",
            str(output_path),
        ]
        subprocess.run(cmd, check=True)
    finally:
        for f in caption_files:
            f.unlink(missing_ok=True)

    return output_path
