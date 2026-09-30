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
