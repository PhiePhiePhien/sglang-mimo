# syntax=docker/dockerfile:1
FROM lmsysorg/sglang:nightly-dev-cu13-20260928-81f27fb3
LABEL org.opencontainers.image.source="https://github.com/PhiePhiePhien/sglang-mimo"
LABEL org.opencontainers.image.description="SGLang nightly with MiMo streaming partial-token fix"
RUN python3 - <<'PY'
from pathlib import Path
import ast

candidates = [
    Path('/sgl-workspace/sglang/python/sglang/srt/function_call/mimo_detector.py'),
    Path('/usr/local/lib/python3.12/site-packages/sglang/srt/function_call/mimo_detector.py'),
    Path('/usr/local/lib/python3.12/dist-packages/sglang/srt/function_call/mimo_detector.py'),
]
paths = list(dict.fromkeys(p.resolve() for p in candidates if p.exists()))
if not paths:
    raise RuntimeError('mimo_detector.py not found')
old = '        if start == -1:\n            if self.current_tool_id > 0:\n                # Already processing tool calls, keep buffering\n                # (more tool calls might come, don\'t discard text yet)\n                return StreamingParseResult(normal_text="")\n            else:\n                # No tool calls seen yet, return as normal text\n                self._buffer = ""\n                return StreamingParseResult(normal_text=current_text)\n\n'
new = '        if start == -1:\n            partial_len = self._ends_with_partial_token(\n                current_text, self.bot_token\n            )\n            if partial_len:\n                self._buffer = current_text[-partial_len:]\n                return StreamingParseResult(\n                    normal_text=current_text[:-partial_len]\n                )\n\n            self._buffer = ""\n            return StreamingParseResult(normal_text=current_text)\n\n'
for p in paths:
    source = p.read_text()
    if source.count(old) != 1:
        raise RuntimeError(f'Expected exactly one original MiMo parser block in {p}')
    patched = source.replace(old, new, 1)
    ast.parse(patched)
    p.write_text(patched)
    print(f'MiMo streaming patch applied: {p}')
PY
