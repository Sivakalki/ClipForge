"""Rule-based script-to-clip matcher (demo version).

Keeps matching logic independent of rendering, per CLAUDE.md conventions:
matcher.py and renderer.py stay separate, independently testable modules.

For each beat in the script, scores every tagged clip by keyword overlap
between the beat's name/text and that clip's tag labels, then picks the
best-scoring clip. Falls back to a hardcoded beat->clip mapping if no clip
scores above zero (e.g. an unlabeled clip library), so the demo never
produces an empty rough cut.
"""

import json
import re
from pathlib import Path

# Fallback mapping used only when keyword scoring finds no match for a beat.
FALLBACK_MAPPING = {
    "Order Placed": "order_placing.mp4",
    "Package Arrival": "order_received.mp4",
    "Unboxing": "unboxing.mp4",
}

STOPWORDS = {"you", "won't", "this", "the", "a", "to", "who", "then"}


def _words(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z']+", text.lower()) if w not in STOPWORDS}


def _load_tags(tags_dir: Path) -> dict[str, dict]:
    tags_by_clip = {}
    for tag_file in sorted(Path(tags_dir).glob("*.json")):
        sidecar = json.loads(tag_file.read_text())
        tags_by_clip[Path(sidecar["file"]).name] = sidecar
    return tags_by_clip


def _score(beat_words: set[str], sidecar: dict) -> int:
    label_words = set()
    for tag in sidecar["tags"]:
        label_words |= _words(tag["label"])
    return len(beat_words & label_words)


def match(script_path: str, tags_dir: str) -> list[tuple[str, str]]:
    """Matches each beat to a distinct clip (no clip is reused across beats),
    so the render step merges the whole tagged library into the rough cut."""
    script = json.loads(Path(script_path).read_text())
    tags_by_clip = _load_tags(tags_dir)
    available = dict(tags_by_clip)

    result = []
    for beat_entry in script["beats"]:
        beat_name = beat_entry["beat"]
        beat_words = _words(beat_name) | _words(beat_entry["text"])

        scored = [
            (clip_name, _score(beat_words, sidecar))
            for clip_name, sidecar in available.items()
        ]
        scored.sort(key=lambda pair: pair[1], reverse=True)

        best_clip, best_score = scored[0] if scored else (None, 0)
        if best_score == 0:
            fallback = FALLBACK_MAPPING.get(beat_name)
            if fallback in available:
                best_clip = fallback

        if best_clip in available:
            del available[best_clip]

        result.append((beat_name, best_clip))
    return result


if __name__ == "__main__":
    demo_dir = Path(__file__).parent
    for beat, clip in match(str(demo_dir / "script.json"), str(demo_dir / "tags")):
        print(f"{beat}: {clip}")
