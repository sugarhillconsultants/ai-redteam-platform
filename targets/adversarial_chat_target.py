"""
targets/adversarial_chat_target.py

A real PyRIT PromptTarget wrapping a plain, unrestricted Claude
conversational call — NOT the injection classifier, a genuinely
different role: this is the "adversarial generator" CrescendoAttack
needs, which produces increasingly escalating prompts based on
feedback from the objective target's previous responses.

FRAMING, stated explicitly rather than left implicit: this target's
job is to generate test prompts for evaluating THIS PROJECT'S OWN
defensive classifier (Project 7's injection screening) — a legitimate,
appropriate security-testing use case, not an attempt to elicit
genuinely harmful content from Claude for its own sake. Claude will
still apply its own normal safety judgment to what it's asked to
generate; this target does not attempt to bypass that, and a Crescendo
run may itself be refused or curtailed by Claude's own judgment about
what a reasonable security-testing prompt-generation task looks like
— itself a real, informative finding if it happens, not a failure to
route around.

Follows the exact same, already-proven pattern as
injection_guardrail_target.py: keyword-only init (PyRIT's brick
contract), implementing the private _send_prompt_to_target_async
method, receiving the full conversation history.

THREE required capabilities found only by attempting real
construction against CrescendoAttack, not documented anywhere read in
advance: supports_multi_turn, supports_editable_history (both found
constructing SelfAskTrueFalseScorer against this target), and
supports_system_prompt (found constructing CrescendoAttack itself).
The third one required actual code, not just a declaration: checking
PyRIT's own real OpenAIChatTarget confirmed system prompts flow
through the same conversation history as a message with role="system"
— but Anthropic's actual API is different from OpenAI's here: it takes
`system` as a SEPARATE top-level parameter to messages.create(), not
as a role inside the messages list. Getting this wrong would likely
have produced a confusing API-level error rather than a clear one, so
this was checked directly against Anthropic's real client rather than
assumed to work the same way as PyRIT's OpenAI-oriented reference
implementation. See docs/incidents.md.
"""

import os

from pyrit.prompt_target import PromptTarget
from pyrit.prompt_target.common.target_configuration import TargetConfiguration, TargetCapabilities
from pyrit.models.messages.message import Message
from pyrit.models.messages.message_piece import MessagePiece


class AdversarialChatTarget(PromptTarget):
    """A plain conversational Claude target — no classification logic,
    just a real chat completion, used as CrescendoAttack's adversarial
    prompt generator."""

    _DEFAULT_CONFIGURATION = TargetConfiguration(
        capabilities=TargetCapabilities(
            supports_multi_turn=True,
            supports_editable_history=True,
            supports_system_prompt=True,
        )
    )

    def __init__(self, *, model="claude-sonnet-4-5", max_tokens=500):
        super().__init__()
        self._model = model
        self._max_tokens = max_tokens

    async def _send_prompt_to_target_async(self, *, normalized_conversation):
        import anthropic

        client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
        workspace_id = os.environ.get("ANTHROPIC_WORKSPACE_ID")

        # Anthropic's API takes `system` as a separate parameter, NOT
        # as a role inside the messages list (unlike OpenAI's format).
        # Extract any system-role message(s) separately; everything
        # else becomes a real user/assistant message.
        system_text_parts = []
        api_messages = []
        for msg in normalized_conversation:
            piece = msg.message_pieces[0]
            text = piece.converted_value or piece.original_value
            if piece.role == "system":
                system_text_parts.append(text)
            else:
                role = "assistant" if piece.role == "assistant" else "user"
                api_messages.append({"role": role, "content": text})

        create_kwargs = {
            "model": self._model,
            "max_tokens": self._max_tokens,
            "messages": api_messages,
            "extra_headers": {"anthropic-workspace-id": workspace_id} if workspace_id else {},
        }
        if system_text_parts:
            create_kwargs["system"] = "\n\n".join(system_text_parts)

        response = client.messages.create(**create_kwargs)

        # Same real finding from docs/incidents.md #9 applies here too
        # — an upstream refusal produces empty content, which must be
        # handled explicitly rather than crashing.
        if not response.content:
            category = getattr(response.stop_details, "category", "unknown") if response.stop_details else "unknown"
            response_text = f"[ADVERSARIAL GENERATOR REFUSED: category={category}]"
        else:
            response_text = response.content[0].text

        current_piece = normalized_conversation[-1].message_pieces[0]
        response_piece = MessagePiece(
            role="assistant",
            original_value=response_text,
            conversation_id=current_piece.conversation_id,
        )
        return [Message(message_pieces=[response_piece])]
