.PHONY: demo prepare tag run web clean

# Tags sample clips, then runs the full matcher -> render pipeline.
demo: tag run

# One-time editorial pass: trims/crops/speeds raw uploads in demo/clips_raw/
# into demo/clips/. Only needed again if you swap in different source footage.
prepare:
	python3 demo/prepare_clips.py

# Writes demo/tags/*.json from demo/clips/*.mp4
tag:
	python3 demo/tag_clips.py

# Matches script.json beats to tagged clips and renders the rough cut.
run:
	python3 demo/run_demo.py

# Starts the local demo UI (single prompt -> generate) at localhost:8000
web:
	python3 demo/webapp/server.py

# Removes generated output (tags + rendered video), keeps source clips.
clean:
	rm -rf demo/tags demo/output demo/__pycache__
