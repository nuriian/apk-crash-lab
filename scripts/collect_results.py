#!/usr/bin/env python3
"""Copy generated videos from cli.py result JSON into ./output/.

Reads the file that captured `cli.py` stdout. Upstream writes runtime logs
to stdout as well as the final result object, so this parser scans for the
LAST line that parses as a JSON object with a "result" key instead of
requiring the whole file to be pure JSON. For stop_at=script/terms/audio,
there are no videos — the payload (script/terms/audio_file/subtitle_path)
is saved as result.json and the step succeeds.

Exits non-zero only when no result object is found at all.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys


def find_result(path: str) -> dict | None:
    with open(path, encoding="utf-8", errors="replace") as f:
        lines = f.read().splitlines()
    for line in reversed(lines):
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict) and "result" in payload:
            return payload
    return None


def parse_args(argv=None) -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--result", required=True, help="captured stdout from cli.py")
    p.add_argument("--output", required=True, help="destination directory")
    return p.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    payload = find_result(args.result)
    if payload is None:
        print("no result JSON object found in cli stdout", file=sys.stderr)
        return 1

    result = payload.get("result", {}) if isinstance(payload, dict) else {}
    videos = result.get("videos") or []

    os.makedirs(args.output, exist_ok=True)
    copied = []
    for i, src in enumerate(videos, start=1):
        if not os.path.isfile(src):
            print(f"missing file, skipping: {src}", file=sys.stderr)
            continue
        dst = os.path.join(args.output, f"video-{i}.mp4")
        shutil.copyfile(src, dst)
        copied.append(dst)
        print(f"copied {src} -> {dst}")

    manifest = {
        "task_id": payload.get("task_id"),
        "videos": copied,
        "script": result.get("script"),
        "terms": result.get("terms"),
        "audio_file": result.get("audio_file"),
        "subtitle_path": result.get("subtitle_path"),
    }
    with open(os.path.join(args.output, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    with open(os.path.join(args.output, "result.json"), "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    if videos and not copied:
        print("result lists videos but none exist on disk", file=sys.stderr)
        return 1
    print(f"done: {len(copied)} video(s) in {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
