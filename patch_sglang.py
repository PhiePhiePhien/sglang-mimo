"""Apply the two narrowly scoped streaming fixes to a known SGLang tree."""
import ast
from pathlib import Path
import sys

MIMO_OLD = '        if start == -1:\n            if self.current_tool_id > 0:\n                # Already processing tool calls, keep buffering\n                # (more tool calls might come, don\'t discard text yet)\n                return StreamingParseResult(normal_text="")\n            else:\n                # No tool calls seen yet, return as normal text\n                self._buffer = ""\n                return StreamingParseResult(normal_text=current_text)\n\n'
MIMO_NEW = '        if start == -1:\n            partial_len = self._ends_with_partial_token(\n                current_text, self.bot_token\n            )\n            if partial_len:\n                self._buffer = current_text[-partial_len:]\n                return StreamingParseResult(\n                    normal_text=current_text[:-partial_len]\n                )\n\n            self._buffer = ""\n            return StreamingParseResult(normal_text=current_text)\n\n'
SSE_OLD = '    delta = StreamDelta(role=role, content=content, reasoning_content=reasoning_content)\n'
SSE_NEW = '    # Suppress only empty content-only events (SGLang issue #29441).\n    # Preserve role, reasoning, finish, logprobs, stop and usage metadata.\n    if (\n        content == ""\n        and role is None\n        and reasoning_content is None\n        and finish_reason is None\n        and logprobs is None\n        and matched_stop is None\n        and usage is None\n    ):\n        return ""\n\n    delta = StreamDelta(role=role, content=content, reasoning_content=reasoning_content)\n'


def apply(root_dirs):
    changes = []
    for relative, old, new in [
        ('sglang/srt/function_call/mimo_detector.py', MIMO_OLD, MIMO_NEW),
        ('sglang/srt/entrypoints/openai/sse_utils.py', SSE_OLD, SSE_NEW),
    ]:
        paths = list(dict.fromkeys((root / relative).resolve() for root in root_dirs if (root / relative).is_file()))
        if not paths:
            raise RuntimeError(f'Cannot find {relative}')
        for path in paths:
            source = path.read_text()
            if source.count(new) == 1:
                print(f'Already patched: {path}')
                continue
            if source.count(old) != 1:
                raise RuntimeError(f'Expected exactly one original patch target in {path}')
            result = source.replace(old, new, 1)
            ast.parse(result)
            changes.append((path, result))
    for path, result in changes:
        path.write_text(result)
        print(f'Applied streaming fix: {path}')


if __name__ == '__main__':
    roots = [Path(p) for p in sys.argv[1:]] or [
        Path('/sgl-workspace/sglang/python'),
        Path('/usr/local/lib/python3.12/site-packages'),
        Path('/usr/local/lib/python3.12/dist-packages'),
    ]
    apply(roots)
