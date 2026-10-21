"""CPU-only regression checks against the actual installed MiMo parser."""
from sglang.srt.function_call.mimo_detector import MiMoDetector
from sglang.srt.entrypoints.openai.protocol import Tool

tool = Tool.model_validate({"type": "function", "function": {"name": "echo", "parameters": {"type": "object", "properties": {"text": {"type": "string"}}}}})
block = '<tool_call><function=echo><parameter=text>hello</parameter></function></tool_call>'
for split in range(1, len('<tool_call>')):
    detector = MiMoDetector()
    first = detector.parse_streaming_increment('before ' + block[:split], [tool])
    assert first.normal_text == 'before ' and not first.calls
    second = detector.parse_streaming_increment(block[split:], [tool])
    assert len(second.calls) == 1 and second.calls[0].name == 'echo'
    tail = detector.parse_streaming_increment('after', [tool])
    assert tail.normal_text == 'after' and detector._buffer == ''
    third = detector.parse_streaming_increment(block[:split], [tool])
    assert not third.normal_text and not third.calls
    fourth = detector.parse_streaming_increment(block[split:], [tool])
    assert len(fourth.calls) == 1 and fourth.calls[0].tool_index == 1
# A possible token prefix that turns out to be ordinary text must not be lost.
detector = MiMoDetector()
assert detector.parse_streaming_increment('text <tool', [tool]).normal_text == 'text '
assert detector.parse_streaming_increment('box>', [tool]).normal_text == '<toolbox>'
print('PASS: all opening-token split positions, repeated calls, trailing text, false prefix')

# Validate emitted SSE, including metadata that must never be suppressed.
import json
from sglang.srt.entrypoints.openai.sse_utils import build_sse_content

base = dict(chunk_id='test', created=1, model='test', index=0)
assert build_sse_content(**base, content='') == ''
for extra, section, key, expected in [
    ({'role': 'assistant'}, 'delta', 'role', 'assistant'),
    ({'reasoning_content': 'thinking'}, 'delta', 'reasoning_content', 'thinking'),
    ({'reasoning_content': ''}, 'delta', 'reasoning_content', ''),
    ({'finish_reason': 'tool_calls'}, 'choice', 'finish_reason', 'tool_calls'),
    ({'finish_reason': 'stop'}, 'choice', 'finish_reason', 'stop'),
    ({'logprobs': {}}, 'choice', 'logprobs', {}),
    ({'usage': {}}, 'root', 'usage', {}),
    ({'matched_stop': 0}, 'choice', 'matched_stop', 0),
    ({'matched_stop': ''}, 'choice', 'matched_stop', ''),
]:
    event = build_sse_content(**base, content='', **extra)
    assert event.startswith('data: ') and event.endswith('\n\n'), extra
    payload = json.loads(event[6:])
    target = payload if section == 'root' else payload['choices'][0]
    if section == 'delta':
        target = target['delta']
    assert target[key] == expected, extra
for content in (None, 'hello', ' '):
    assert build_sse_content(**base, content=content).startswith('data: ')
print('PASS: empty-content SSE suppression and role/reasoning/finish/logprobs/usage/matched_stop preservation')

# PR #41649: test real parsing for nullable/union types, in both modes.
from sglang.srt.function_call.mimo_detector import _get_param_type
cases = [
    (['string', 'null'], 'celsius', 'celsius'),
    (['null', 'integer'], '7', 7),
    (['integer', 'null'], '7', 7),
    (['string', 'null'], 'null', None),
    (['null'], 'fallback', 'fallback'),
    ([], 'fallback', 'fallback'),
    ('integer', '7', 7),
    ('string', '7', '7'),
]
for schema_type, value, expected in cases:
    tools = [Tool.model_validate({'type': 'function', 'function': {
        'name': 'echo', 'parameters': {'type': 'object', 'properties': {
            'text': {'type': schema_type}
        }}
    }})]
    text = f'<tool_call><function=echo><parameter=text>{value}</parameter></function></tool_call>'
    for streaming in (False, True):
        detector = MiMoDetector()
        if streaming:
            calls = []
            for character in text:
                calls.extend(detector.parse_streaming_increment(character, tools).calls)
        else:
            calls = detector.detect_and_parse(text, tools).calls
        assert len(calls) == 1, (schema_type, streaming)
        actual = json.loads(calls[0].parameters)['text']
        assert actual == expected and type(actual) is type(expected), (schema_type, streaming, actual)
print('PASS: PR #41649 union/nullable/plain types in full and character-level streaming parsing')
