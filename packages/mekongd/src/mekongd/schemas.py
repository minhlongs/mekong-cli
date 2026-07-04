"""Anthropic Messages API pydantic schemas — v1."""

from __future__ import annotations

from typing import Literal, Optional, Union

from pydantic import BaseModel, Field


class ContentBlock(BaseModel):
    """Text content block."""

    type: Literal["text"] = "text"
    text: str


class Message(BaseModel):
    """Single turn in conversation."""

    role: Literal["user", "assistant"]
    content: Union[str, list[ContentBlock]]


class MessagesRequest(BaseModel):
    """POST /v1/messages body (Anthropic schema)."""

    model: str
    messages: list[Message]
    max_tokens: int = 1024
    stream: bool = False
    system: Optional[Union[str, list[ContentBlock]]] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    stop_sequences: Optional[list[str]] = None

    def get_system_text(self) -> str:
        if not self.system:
            return ""
        if isinstance(self.system, str):
            return self.system
        return "".join(cb.text for cb in self.system)


class Usage(BaseModel):
    input_tokens: int = 0
    output_tokens: int = 0


class SignalRequest(BaseModel):
    """POST /v1/signals body — operator feedback loop (Pillar 3)."""

    kind: Literal["good", "bad"]
    note: str = Field(default="", max_length=500)
    model: str = Field(default="", max_length=120)


class MessagesResponse(BaseModel):
    """Non-streaming response (Anthropic schema)."""

    id: str
    type: Literal["message"] = "message"
    role: Literal["assistant"] = "assistant"
    content: list[ContentBlock]
    model: str
    stop_reason: Literal["end_turn", "max_tokens", "stop_sequence"] = "end_turn"
    stop_sequence: Optional[str] = None
    usage: Usage = Field(default_factory=Usage)


# SSE event payloads for streaming (subset).
class MessageStartEvent(BaseModel):
    type: Literal["message_start"] = "message_start"
    message: MessagesResponse


class ContentBlockStartEvent(BaseModel):
    type: Literal["content_block_start"] = "content_block_start"
    index: int = 0
    content_block: ContentBlock


class ContentBlockDelta(BaseModel):
    type: Literal["text_delta"] = "text_delta"
    text: str


class ContentBlockDeltaEvent(BaseModel):
    type: Literal["content_block_delta"] = "content_block_delta"
    index: int = 0
    delta: ContentBlockDelta


class ContentBlockStopEvent(BaseModel):
    type: Literal["content_block_stop"] = "content_block_stop"
    index: int = 0


class MessageDeltaPayload(BaseModel):
    stop_reason: Literal["end_turn", "max_tokens", "stop_sequence"] = "end_turn"
    stop_sequence: Optional[str] = None


class MessageDeltaUsage(BaseModel):
    """Anthropic message_delta usage — output_tokens only per strict spec."""

    output_tokens: int = 0


class MessageDeltaEvent(BaseModel):
    type: Literal["message_delta"] = "message_delta"
    delta: MessageDeltaPayload
    usage: MessageDeltaUsage = Field(default_factory=MessageDeltaUsage)


class MessageStopEvent(BaseModel):
    type: Literal["message_stop"] = "message_stop"
