#!/usr/bin/env python3
"""Copy generated videos from cli.py result JSON into ./output/.

Reads the file that captured `cli.py` stdout. Upstream writes runtime logs
to stdout as well as the final result object, so this parser scans for the
LAST line that parses as a JSON object with a "result" (single task) or
"tasks" (batch mode) key instead of requiring the whole file to be pure
JSON. For stop_at=script/terms/audio, there are no videos — the payload
(script/terms/audio_file/subtitle_path) is saved as result.json and the
step succeeds. Batch audio/subtitle files are copied per task as
task-<index>-<basename>.

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
        if isinstance(payload, dict) and ("result" in payload or "tasks" in payload):
            return payload
    return None


def copy_one(src: str, dst: str) -> str | None:
    if not src or not os.path.isfile(src):
        if src:
            print(f"missing file, skipping: {src}", file=sys.stderr)
        return None
    shutil.copyfile(src, dst)
    print(f"copied {src} -> {dst}")
    return dst


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

    os.makedirs(args.output, exist_ok=True)

    # Batch mode: {total, succeeded, failed, tasks: [{index, task_id,
    # status, result, failed_stage, error}]}.
    if "tasks" in payload:
        summaries = []
        n_files = 0
        for entry in payload.get("tasks") or []:
            result = entry.get("result") or {}
            files = []
            for key in ("videos",):
                for src in result.get(key) or []:
                    dst = copy_one(
                        src,
                        os.path.join(
                            args.output,
                            f"task-{entry.get('index')}-{os.path.basename(src)}",
                        ),
                    )
                    if dst:
                        files.append(dst)
                        n_files += 1
            for key in ("audio_file", "subtitle_path"):
                src = result.get(key)
                if src:
                    dst = copy_one(
                        src,
                        os.path.join(
                            args.output,
                            f"task-{entry.get('index')}-{os.path.basename(src)}",
                        ),
                    )
                    if dst:
                        files.append(dst)
                        n_files += 1
            summaries.append(
                {
                    "index": entry.get("index"),
                    "task_id": entry.get("task_id"),
                    "status": entry.get("status"),
                    "failed_stage": entry.get("failed_stage"),
                    "error": entry.get("error"),
                    "files": files,
                    "script": result.get("script") if isinstance(result, dict) else None,
                }
            )
        with open(os.path.join(args.output, "manifest.json"), "w", encoding="utf-8") as f:
            json.dump(
                {
                    "mode": "batch",
                    "total": payload.get("total"),
                    "succeeded": payload.get("succeeded"),
                    "failed": payload.get("failed"),
                    "tasks": summaries,
                },
                f,
                ensure_ascii=False,
                indent=2,
            )
        with open(os.path.join(args.output, "result.json"), "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        print(f"done: batch {payload.get('succeeded')}/{payload.get('total')} ok, {n_files} file(s)")
        return 0 if not payload.get("failed") else 1

    result = payload.get("result", {}) if isinstance(payload, dict) else {}
    videos = result.get("videos") or []

    copied = []
    for i, src in enumerate(videos, start=1):
        dst = copy_one(src, os.path.join(args.output, f"video-{i}.mp4"))
        if dst:
            copied.append(dst)

    manifest = {
        "task_id": payload.get("task_id"),
        "videos": copied,
        "script": result.get("script"),
        "terms": result.get("terms"),
        "materials": result.get("materials"),
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
