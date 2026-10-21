# SGLang MiMo tool-stream fixes

Base: `lmsysorg/sglang:nightly-dev-cu13-20261021-c1c287a4` (linux/amd64).
Only two Python files change; CUDA kernels and other dependencies are inherited.

- `mimo_detector.py`: normalize JSON Schema union parameter types using [PR #41649](https://github.com/sgl-project/sglang/pull/41649), and preserve partial `<tool_call>` prefixes and release ordinary text after tool calls ([#33189](https://github.com/sgl-project/sglang/pull/33189)).
- `sse_utils.py`: suppress empty content-only SSE events ([#29441](https://github.com/sgl-project/sglang/issues/29441)); retain role, reasoning, finish, logprobs, usage and matched-stop metadata. Tool-call events use the existing separate serialization path.

The build fails on unexpected source. Regression checks run inside the built image before publication.
This is a targeted workaround, not a guarantee to resolve HTTP socket aborts.
GPU inference and end-to-end Open WebUI/GPUStack streaming have not been tested.

## GPUStack image

```text
ghcr.io/phiephiephien/sglang-mimo:20261021-pr41649
```

`latest` points to the same build. Superseded image versions are removed after successful publication and verification of the replacement.
Select the new image in your SGLang backend version and retain your existing entrypoint/model settings.

## Local build and verification

```sh
docker build --platform linux/amd64 -t sglang-mimo:toolstream-fix .
docker run --rm --entrypoint python3 -v "$PWD/test_streaming.py:/tmp/test_streaming.py:ro" sglang-mimo:toolstream-fix /tmp/test_streaming.py
```

For deployment validation, inspect a streaming tool-call request with `curl -N`: check actual tool calls, text after calls, the finish event and final `[DONE]`. Persistent `UND_ERR_SOCKET` requires separate server/proxy connection diagnostics.

Base linux/amd64 digest: `sha256:a8eedda74b54f7dfecc445ee66d298f8d8f6f50192201a53b0a6dd7571ff8d26`.
PR #41649 behavior uses the first non-null union entry, falling back to string when none exists.
