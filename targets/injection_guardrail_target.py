"""
targets/injection_guardrail_target.py

A real PyRIT PromptTarget wrapping the exact injection-screening
classifier already built and proven in Project 7
(multi-agent-security-platform/guardrails/injection_screening.py) —
not a reimplementation. This lets PyRIT's real dataset, execution, and
scoring infrastructure send adversarial prompts through the actual
system under test.

CORRECTED after two real, confirmed API findings from PyRIT 1.1.0
itself (not guessed): (1) PromptTarget subclasses must have
keyword-only __init__ parameters (PyRIT's own "brick contract"
enforcement), and (2) the actual method to implement is the PRIVATE
`_send_prompt_to_target_async`, not the public `send_prompt_async`
(which is a concrete base-class wrapper handling validation/
normalization before calling this). `_send_prompt_to_target_async`
receives the FULL conversation history, not just the latest message —
genuinely useful for this project's later multi-turn exploit testing.

Dependency-injected classifier_fn, matching the exact pattern already
used throughout this whole portfolio (Projects 6 and 7's
data_source-injection design) — testable here with a mock, and later
pointed at the real llm_injection_classifier for genuine, live
adversarial testing.
"""

from pyrit.prompt_target import PromptTarget
from pyrit.models.messages.message import Message
from pyrit.models.messages.message_piece import MessagePiece


class InjectionGuardrailTarget(PromptTarget):
    """Wraps Project 7's classifier as a PyRIT-attackable target.
    classifier_fn signature matches guardrails/injection_screening.py's
    real functions exactly: (text: str) -> (flagged: bool, reasoning: str)."""

    def __init__(self, *, classifier_fn):
        super().__init__()
        self._classifier_fn = classifier_fn

    async def _send_prompt_to_target_async(self, *, normalized_conversation):
        # The current message is the last element of the full conversation history.
        current_message = normalized_conversation[-1]
        piece = current_message.message_pieces[0]
        prompt_text = piece.converted_value or piece.original_value

        flagged, reasoning = self._classifier_fn(prompt_text)

        response_text = f"FLAGGED: {reasoning}" if flagged else f"SAFE: {reasoning}"

        response_piece = MessagePiece(
            role="assistant",
            original_value=response_text,
            conversation_id=piece.conversation_id,
        )
        return [Message(message_pieces=[response_piece])]
