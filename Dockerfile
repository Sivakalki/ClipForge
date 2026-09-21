# ClipForge demo UI -- see demo/README.md for what this actually does.
# Builds a self-contained image: ffmpeg + the pre-tagged clip library baked
# in, so the container needs no setup step at runtime beyond starting the
# server.

FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .

# Bake the tag sidecars in at build time (idempotent) so the pipeline has
# everything it needs on first request, regardless of what's committed.
RUN python3 demo/tag_clips.py

ENV PORT=7860
EXPOSE 7860

CMD ["python3", "demo/webapp/server.py"]
