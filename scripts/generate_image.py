#!/usr/bin/env python3
"""Generate an image with Agnes AI's OpenAI-compatible image endpoint."""

from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import os
import ssl
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


DEFAULT_BASE_URL = "https://apihub.agnes-ai.com/v1"
DEFAULT_MODEL = "agnes-image-2.1-flash"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate images with Agnes AI.")
    parser.add_argument("--prompt", required=True, help="Text prompt for image generation.")
    parser.add_argument("--output", default="agnes-image.png", help="Output image path.")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Agnes image model name.")
    parser.add_argument("--size", default="1024x1024", help="Image size, for example 1024x1024.")
    parser.add_argument("--base-url", default=os.environ.get("AGNES_AI_BASE_URL", DEFAULT_BASE_URL))
    parser.add_argument("--api-key", default=os.environ.get("AGNES_AI_API_KEY"))
    parser.add_argument(
        "--input-image",
        help="Optional source image path or URL for image-to-image capable requests.",
    )
    parser.add_argument(
        "--insecure",
        action="store_true",
        help="Skip TLS certificate verification when the local certificate store is broken.",
    )
    parser.add_argument("--raw-json", action="store_true", help="Print the full API response.")
    return parser.parse_args()


def local_image_to_data_url(path: Path) -> str:
    mime_type = mimetypes.guess_type(path.name)[0] or "image/png"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "model": args.model,
        "prompt": args.prompt,
        "size": args.size,
    }

    if args.input_image:
        if args.input_image.startswith(("http://", "https://", "data:")):
            payload["image"] = args.input_image
        else:
            payload["image"] = local_image_to_data_url(Path(args.input_image))

    return payload


def request_json(
    url: str,
    api_key: str,
    payload: dict[str, Any],
    context: ssl.SSLContext | None,
) -> dict[str, Any]:
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=180, context=context) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"Agnes API HTTP {exc.code}: {error_body}") from exc
    except urllib.error.URLError as exc:
        raise SystemExit(f"Agnes API request failed: {exc.reason}") from exc


def extract_image(response: dict[str, Any], context: ssl.SSLContext | None) -> bytes:
    data = response.get("data")
    if not isinstance(data, list) or not data:
        raise SystemExit(f"Agnes API response did not include image data: {json.dumps(response)}")

    first = data[0]
    if not isinstance(first, dict):
        raise SystemExit(f"Unexpected Agnes image item: {json.dumps(first)}")

    if isinstance(first.get("b64_json"), str):
        return base64.b64decode(first["b64_json"])

    if isinstance(first.get("url"), str):
        with urllib.request.urlopen(first["url"], timeout=180, context=context) as response_url:
            return response_url.read()

    raise SystemExit(f"Agnes image item had no b64_json or url: {json.dumps(first)}")


def main() -> int:
    args = parse_args()

    if not args.api_key:
        print("Set AGNES_AI_API_KEY or pass --api-key.", file=sys.stderr)
        return 2

    endpoint = args.base_url.rstrip("/") + "/images/generations"
    context = ssl._create_unverified_context() if args.insecure else None
    response = request_json(endpoint, args.api_key, build_payload(args), context)

    if args.raw_json:
        print(json.dumps(response, ensure_ascii=False, indent=2))

    image_bytes = extract_image(response, context)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(image_bytes)
    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
