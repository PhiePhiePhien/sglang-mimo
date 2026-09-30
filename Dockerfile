# syntax=docker/dockerfile:1
FROM lmsysorg/sglang:nightly-dev-cu13-20260928-81f27fb3
LABEL org.opencontainers.image.source="https://github.com/PhiePhiePhien/sglang-mimo"
LABEL org.opencontainers.image.description="SGLang nightly with MiMo streaming and empty-content SSE fixes"
RUN --mount=type=bind,source=patch_sglang.py,target=/tmp/patch_sglang.py python3 /tmp/patch_sglang.py
