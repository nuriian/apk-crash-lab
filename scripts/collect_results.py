#!/usr/bin/env python3
"""Copy generated videos from cli.py result JSON into ./output/.

Reads the JSON object printed by `cli.py` to stdout, resolves the
`result.videos` absolute paths, copies every mp4 into the output dir,
and writes a small manifest.json. Exits non-zero when no video found.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys


def parse_args(argv=None) -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--result", required=True, help="stdout JSON from cli.py")
    p.add_argument("--output", required=True, help="destination directory")
    return p.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    with open(args.result, encoding="utf-8") as f:
        payload = json.load(f)

    result = payload.get("result", {}) if isinstance(payload, dict) else {}
    videos = result.get("videos") or []
    if not videos:
        print(
            f"no videos in result (failed_stage={result.get('failed_stage')}, "
            f"error={result.get('error')})",
            file=sys.stderr,
        )
        return 1

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
    }
    with open(os.path.join(args.output, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    if not copied:
        return 1
    print(f"done: {len(copied)} video(s) in {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
