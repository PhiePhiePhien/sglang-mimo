# SGLang MiMo streaming fix

Base: `lmsysorg/sglang:nightly-dev-cu13-20260928-81f27fb3` (linux/amd64).
Only `mimo_detector.py` is patched; CUDA kernels and other dependencies are inherited.
Buffers partial `<tool_call>` prefixes and releases ordinary text after tool calls.
The build fails if the expected original parser block is absent. CPU regression checks run before publication.

## GPUStack image

```text
ghcr.io/phiephiephien/sglang-mimo:20260928-streamfix
```

Select this image in your SGLang backend version. Retain your existing entrypoint and model settings.
GPU inference has not been validated by this CPU-only CI job.

## Local build

```sh
docker build --platform linux/amd64 -t sglang-mimo:streamfix .
docker run --rm --entrypoint python3 -v "$PWD/test_streaming.py:/tmp/test_streaming.py:ro" sglang-mimo:streamfix /tmp/test_streaming.py
```
