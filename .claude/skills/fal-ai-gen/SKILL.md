---
name: fal-ai
description: Generate images, videos, and audio via fal.ai API (FLUX, SDXL, Whisper, etc.)
---

# fal.ai API Skill

Generate images, videos, and transcripts using fal.ai's API.

## Setup

```bash
export FAL_KEY="your-api-key"
```

## Available Models

| Model         | Endpoint                              | Type         |
| ------------- | ------------------------------------- | ------------ |
| flux-schnell  | `fal-ai/flux/schnell`                 | Image (fast) |
| flux-dev      | `fal-ai/flux/dev`                     | Image        |
| flux-pro      | `fal-ai/flux-pro/v1.1-ultra`          | Image (2K)   |
| fast-sdxl     | `fal-ai/fast-sdxl`                    | Image        |
| recraft-v3    | `fal-ai/recraft-v3`                   | Image        |
| minimax-video | `fal-ai/minimax-video/image-to-video` | Video        |
| wan-video     | `fal-ai/wan/v2.1/1.3b/text-to-video`  | Video        |
| whisper       | `fal-ai/whisper`                      | Audio        |

## Queue-based API Pattern

```bash
# 1. Submit
curl -X POST "https://queue.fal.run/fal-ai/flux/dev" \
  -H "Authorization: Key $FAL_KEY" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "cyberpunk cityscape", "image_size": "landscape_16_9"}'

# 2. Poll status
curl "https://queue.fal.run/fal-ai/flux/dev/requests/$REQUEST_ID/status" \
  -H "Authorization: Key $FAL_KEY"

# 3. Get result
curl "https://queue.fal.run/fal-ai/flux/dev/requests/$REQUEST_ID" \
  -H "Authorization: Key $FAL_KEY"
```

## Parameters

| Parameter  | Default          | Description             |
| ---------- | ---------------- | ----------------------- |
| prompt     | required         | Image/video description |
| model      | "flux-dev"       | Model name              |
| image_size | "landscape_16_9" | Preset size             |
| num_images | 1                | Number of images        |
| seed       | None             | Random seed             |
