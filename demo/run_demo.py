"""Single entry point that ties the demo pipeline together end to end.

    python demo/run_demo.py

Runs matcher.py against script.json and the tags in /demo/tags/, then
passes the result to render.py. Prints readable step-by-step output --
this is what gets screen-recorded for the explainer video.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from matcher import match  # noqa: E402
from render import render  # noqa: E402

DEMO_DIR = Path(__file__).parent
SCRIPT_PATH = DEMO_DIR / "script.json"
TAGS_DIR = DEMO_DIR / "tags"
CLIPS_DIR = DEMO_DIR / "clips"
AUDIO_PATH = DEMO_DIR.parent / "assets" / "trending_audio.mp3"
OUTPUT_PATH = DEMO_DIR / "output" / "rough_cut.mp4"


def main():
    print("=" * 60)
    print("ClipForge demo -- offline rough-cut pipeline")
    print("=" * 60)

    print("\n[1/3] Matching script beats to tagged clips...")
    matches = match(str(SCRIPT_PATH), str(TAGS_DIR))
    for beat, clip in matches:
        print(f"      {beat:16s} -> {clip}")

    clip_order = [CLIPS_DIR / clip for _, clip in matches]
    missing = [c for c in clip_order if not c.exists()]
    if missing:
        print(f"\nERROR: missing clip file(s): {[str(m) for m in missing]}")
        sys.exit(1)

    script = json.loads(SCRIPT_PATH.read_text())
    caption_by_beat = {b["beat"]: b["text"] for b in script["beats"]}
    captions = [caption_by_beat.get(beat) for beat, _ in matches]

    print("\n[2/3] Clip order for render (all clips merged, captioned):")
    for i, (clip, caption) in enumerate(zip(clip_order, captions), 1):
        print(f"      {i}. {clip.name:24s} \"{caption}\"")

    print("\n[3/3] Rendering...")
    print(f"      video clips : {len(clip_order)} (merged, trimmed + cropped to 1080x1920)")
    print(f"      audio track : {AUDIO_PATH.name} (looped to cover full length)")
    output = render(clip_order, AUDIO_PATH, OUTPUT_PATH, captions=captions)

    print("\n" + "=" * 60)
    print(f"Done. Rough cut written to: {output.resolve()}")
    print("=" * 60)


if __name__ == "__main__":
    main()
