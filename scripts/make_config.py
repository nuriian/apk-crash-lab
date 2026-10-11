#!/usr/bin/env python3
"""Generate upstream/config.toml from config.example.toml + workflow inputs.

Only overrides explicitly provided values; everything else keeps upstream
defaults. Values are injected with plain-text substitution (no TOML library
needed on the runner) and TOML-escaped.
"""

from __future__ import annotations

import argparse
import re
import sys


def toml_str(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def set_app_key(text: str, key: str, rendered: str) -> str:
    """Replace `key = ...` inside the [app] section only."""
    lines = text.split("\n")
    in_app = False
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("["):
            in_app = stripped == "[app]"
            continue
        if in_app and re.match(rf"^{re.escape(key)}\s*=", stripped):
            lines[i] = f"{key} = {rendered}"
            return "\n".join(lines)
    raise SystemExit(f"key not found in [app] section: {key}")


def parse_args(argv=None) -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--example", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--llm-provider", default="")
    p.add_argument("--llm-api-key", default="")
    p.add_argument("--llm-model", default="")
    p.add_argument("--llm-base-url", default="")
    p.add_argument("--pexels-key", default="")
    p.add_argument("--pixabay-key", default="")
    return p.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    with open(args.example, encoding="utf-8") as f:
        text = f.read()

    lines = text.split("\n")
    for i, line in enumerate(lines):
        if re.match(r"^log_level\s*=", line.strip()):
            lines[i] = 'log_level = "INFO"'
            break
    else:
        raise SystemExit("top-level key not found: log_level")
    text = "\n".join(lines)

    provider = args.llm_provider.strip().lower()
    if provider:
        text = set_app_key(text, "llm_provider", toml_str(provider))
        if args.llm_api_key:
            # Convention across providers: <provider>_api_key
            # (moonshot_api_key, gemini_api_key, groq_api_key, ...).
            text = set_app_key(
                text, f"{provider}_api_key", toml_str(args.llm_api_key)
            )
        if args.llm_model:
            text = set_app_key(
                text, f"{provider}_model_name", toml_str(args.llm_model)
            )
        if args.llm_base_url:
            text = set_app_key(
                text, f"{provider}_base_url", toml_str(args.llm_base_url)
            )

    if args.pexels_key:
        text = set_app_key(
            text, "pexels_api_keys", f"[{toml_str(args.pexels_key)}]"
        )
    if args.pixabay_key:
        text = set_app_key(
            text, "pixabay_api_keys", f"[{toml_str(args.pixabay_key)}]"
        )

    with open(args.output, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
