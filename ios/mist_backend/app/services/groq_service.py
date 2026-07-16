import json
from typing import Any

from groq import Groq

from app.config import settings

_client = Groq(api_key=settings.groq_api_key)


def chat(
    messages: list[dict[str, Any]],
    tools: list[dict[str, Any]] | None = None,
    tool_choice: str = "auto",
    temperature: float = 0.7,
    response_format: dict[str, Any] | None = None,
):
    """Single call into Groq's chat completions endpoint. Returns the raw
    message object so callers can inspect both `content` and `tool_calls`."""
    kwargs: dict[str, Any] = {
        "model": settings.mist_model,
        "messages": messages,
        "temperature": temperature,
    }
    if tools:
        kwargs["tools"] = tools
        kwargs["tool_choice"] = tool_choice
    if response_format:
        kwargs["response_format"] = response_format

    completion = _client.chat.completions.create(**kwargs)
    return completion.choices[0].message


def chat_json(messages: list[dict[str, Any]], temperature: float = 0.2) -> dict[str, Any]:
    """Call Groq and force a JSON object back. Used by services like
    emotion detection that need structured, parseable output."""
    message = chat(
        messages,
        temperature=temperature,
        response_format={"type": "json_object"},
    )
    return json.loads(message.content)
