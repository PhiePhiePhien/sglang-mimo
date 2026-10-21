# syntax=docker/dockerfile:1
FROM lmsysorg/sglang:nightly-dev-cu13-20261021-c1c287a4@sha256:a8eedda74b54f7dfecc445ee66d298f8d8f6f50192201a53b0a6dd7571ff8d26
LABEL org.opencontainers.image.source="https://github.com/PhiePhiePhien/sglang-mimo"
LABEL org.opencontainers.image.description="SGLang nightly with MiMo union-type, streaming and empty-content SSE fixes"
RUN --mount=type=bind,source=patch_sglang.py,target=/tmp/patch_sglang.py python3 /tmp/patch_sglang.py
