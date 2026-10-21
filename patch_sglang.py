"""Apply the streaming and MiMo union-type fixes to a known SGLang tree."""
import ast
from pathlib import Path
import sys

MIMO_OLD = '''        if start == -1:
            if self.current_tool_id > 0:
                # Already processing tool calls, keep buffering
                # (more tool calls might come, don't discard text yet)
                return StreamingParseResult(normal_text="")
            else:
                # No tool calls seen yet, return as normal text
                self._buffer = ""
                return StreamingParseResult(normal_text=current_text)

'''
MIMO_NEW = '''        if start == -1:
            partial_len = self._ends_with_partial_token(
                current_text, self.bot_token
            )
            if partial_len:
                self._buffer = current_text[-partial_len:]
                return StreamingParseResult(
                    normal_text=current_text[:-partial_len]
                )

            self._buffer = ""
            return StreamingParseResult(normal_text=current_text)

'''
SSE_OLD = '''    delta = StreamDelta(role=role, content=content, reasoning_content=reasoning_content)
'''
SSE_NEW = '''    # Suppress only empty content-only events (SGLang issue #29441).
    # Preserve role, reasoning, finish, logprobs, stop and usage metadata.
    if (
        content == ""
        and role is None
        and reasoning_content is None
        and finish_reason is None
        and logprobs is None
        and matched_stop is None
        and usage is None
    ):
        return ""

    delta = StreamDelta(role=role, content=content, reasoning_content=reasoning_content)
'''


UNION_OLD = '''                return props[param_name].get("type", "string")
'''
UNION_NEW = '''                param_type = props[param_name].get("type", "string")
                if isinstance(param_type, list):
                    # JSON Schema union type (e.g. ["string", "null"]):
                    # use the first non-null entry for value conversion
                    non_null = [t for t in param_type if t != "null"]
                    return non_null[0] if non_null else "string"
                return param_type
'''


def apply(root_dirs):
    changes = {}
    for relative, old, new in [
        ('sglang/srt/function_call/mimo_detector.py', MIMO_OLD, MIMO_NEW),
        ('sglang/srt/function_call/mimo_detector.py', UNION_OLD, UNION_NEW),
        ('sglang/srt/entrypoints/openai/sse_utils.py', SSE_OLD, SSE_NEW),
    ]:
        paths = list(dict.fromkeys((root / relative).resolve() for root in root_dirs if (root / relative).is_file()))
        if not paths:
            raise RuntimeError(f'Cannot find {relative}')
        for path in paths:
            source = changes.get(path, path.read_text())
            if source.count(new) == 1:
                print(f'Already patched: {path}')
                continue
            if source.count(old) != 1:
                raise RuntimeError(f'Expected exactly one original patch target in {path}')
            result = source.replace(old, new, 1)
            ast.parse(result)
            changes[path] = result
    for path, result in changes.items():
        path.write_text(result)
        print(f'Applied streaming fix: {path}')


if __name__ == '__main__':
    roots = [Path(p) for p in sys.argv[1:]] or [
        Path('/sgl-workspace/sglang/python'),
        Path('/usr/local/lib/python3.12/site-packages'),
        Path('/usr/local/lib/python3.12/dist-packages'),
    ]
    apply(roots)
