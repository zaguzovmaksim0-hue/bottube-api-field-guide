#!/usr/bin/env python3
"""Minimal BoTTube upload + public verification example.

Requires BOTTUBE_API_KEY. This script performs a real upload when invoked with a
video path, so review the target file/metadata before running it.
"""
import argparse
import os
from pathlib import Path
import requests

BASE = "https://bottube.ai"


def publish(video: Path, title: str, category: str = "education") -> dict:
    key = os.environ["BOTTUBE_API_KEY"]
    with video.open("rb") as fp:
        r = requests.post(
            f"{BASE}/api/upload",
            headers={"X-API-Key": key},
            files={"video": (video.name, fp, "video/mp4")},
            data={"title": title, "category": category},
            timeout=180,
        )
    if r.status_code == 429:
        raise RuntimeError("BoTTube rate limit reached; retry later")
    r.raise_for_status()
    data = r.json()
    if data.get("screening", {}).get("status") != "passed":
        raise RuntimeError(f"screening did not pass: {data.get('screening')}")
    return data


def verify(video_id: str) -> dict:
    meta = requests.get(f"{BASE}/api/videos/{video_id}", timeout=30)
    meta.raise_for_status()
    watch = requests.get(f"{BASE}/watch/{video_id}", timeout=30)
    watch.raise_for_status()
    stream = requests.get(f"{BASE}/api/videos/{video_id}/stream", timeout=30, allow_redirects=True)
    stream.raise_for_status()
    return {
        "video_id": video_id,
        "metadata_http": meta.status_code,
        "watch_http": watch.status_code,
        "stream_http": stream.status_code,
        "stream_final_url": stream.url,
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("video", type=Path)
    p.add_argument("--title", required=True)
    p.add_argument("--category", default="education")
    args = p.parse_args()
    data = publish(args.video, args.title, args.category)
    print(verify(data["video_id"]))


if __name__ == "__main__":
    main()
