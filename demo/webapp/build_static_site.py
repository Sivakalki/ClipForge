"""Assembles demo/webapp/static-site/ into a fully static, backend-free
deployable copy of the demo UI -- for hosting on GitHub Pages, Netlify,
Cloudflare Pages, or any plain static host (all free, no paid tier needed).

Copies the raw footage and the pre-rendered rough cut in alongside the
static-site/index.html (which plays the same matching animation as the
live demo, then reveals the bundled video instead of calling a server).
Re-run this whenever demo/clips_raw/ or demo/output/rough_cut.mp4 change.

Run: python3 demo/webapp/build_static_site.py
"""

import shutil
from pathlib import Path

DEMO_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = DEMO_DIR / "clips_raw"
OUTPUT_VIDEO = DEMO_DIR / "output" / "rough_cut.mp4"
SITE_DIR = Path(__file__).resolve().parent / "static-site"


def main():
    if not OUTPUT_VIDEO.exists():
        raise SystemExit(
            f"{OUTPUT_VIDEO} not found -- run `python3 demo/run_demo.py` first "
            "to render the rough cut before building the static site."
        )

    site_raw = SITE_DIR / "raw"
    site_output = SITE_DIR / "output"
    site_raw.mkdir(parents=True, exist_ok=True)
    site_output.mkdir(parents=True, exist_ok=True)

    for clip in RAW_DIR.glob("*.mp4"):
        shutil.copy2(clip, site_raw / clip.name)
        print(f"copied {clip.name} -> static-site/raw/")

    shutil.copy2(OUTPUT_VIDEO, site_output / "rough_cut.mp4")
    print(f"copied {OUTPUT_VIDEO.name} -> static-site/output/")

    print(f"\nStatic site ready at {SITE_DIR}")
    print("Preview locally with: python3 -m http.server -d demo/webapp/static-site 8080")


if __name__ == "__main__":
    main()
