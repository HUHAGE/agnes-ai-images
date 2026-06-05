---
name: agnes-ai-images
description: Use Agnes AI to generate or edit images with the agnes-image-2.0-flash model through the OpenAI-compatible https://apihub.agnes-ai.com/v1 API. Trigger when the user asks to generate images with Agnes, Agnes AI, agnes-image-2.0-flash, agnes-2.0-flash image generation, or the Agnes API.
---

# Agnes AI Images

Use this skill when a user wants image generation through Agnes AI.

## Core Assumptions

- API base URL: `https://apihub.agnes-ai.com/v1`
- Image endpoint: `/images/generations`
- Default image model: `agnes-image-2.0-flash`
- If the user says `agnes-2.0-flash` for image generation, treat it as `agnes-image-2.0-flash` unless they explicitly confirm a different image model.
- Do not hard-code API keys in skill files, scripts, generated examples, or logs.

## Required Credential

Set the API key in the shell before running the script:

```bash
export AGNES_AI_API_KEY="..."
```

If the key is only provided in the conversation, pass it as an environment variable for the command invocation and avoid writing it to disk.

## Generate An Image

Use the bundled script for deterministic API calls:

```bash
python3 scripts/generate_image.py \
  --prompt "A clean product render of a white ceramic desk lamp" \
  --output ./outputs/lamp.png
```

Common options:

- `--model`: defaults to `agnes-image-2.0-flash`
- `--size`: defaults to `1024x1024`
- `--input-image`: optional local image path or URL for image-to-image capable requests
- `--output`: output file path; defaults to `agnes-image.png`
- `--raw-json`: print the full API response JSON for debugging

## Workflow

1. Clarify the prompt only if the requested image is underspecified enough to make the result unusable.
2. Run `scripts/generate_image.py` with the prompt, output path, and any requested size or input image.
3. Confirm the generated file path. If generation fails, report the API error body without exposing the API key.

## Notes

- The API is OpenAI-style compatible, but provider-specific fields may change. If Agnes returns a validation error, inspect the JSON error and adjust the request body in `scripts/generate_image.py`.
- Prefer storing generated images under an `outputs/` directory inside the current workspace unless the user asks for another location.
