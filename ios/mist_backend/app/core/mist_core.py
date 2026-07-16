import json
from datetime import datetime, timezone

from app.config import settings
from app.storage.json_store import read_json, write_json
from app.services import groq_service, math_service, weather_service, search_service, emotion_service

_DATA = settings.data_dir
PERSONALITY_PATH = _DATA / "personality.json"
USER_PROFILE_PATH = _DATA / "user_profile.json"
CONVERSATION_PATH = _DATA / "conversation_knowledge.json"
KNOWLEDGE_PATH = _DATA / "knowledge_base.json"
EMOTIONAL_STATE_PATH = _DATA / "emotional_state.json"

MAX_TOOL_ITERATIONS = 3

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get the current weather for a named location.",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "City or place name, e.g. 'Abuja' or 'Lagos, Nigeria'.",
                    }
                },
                "required": ["location"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "solve_math",
            "description": "Solve a math expression or equation exactly (arithmetic, algebra, simplification).",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "e.g. '2*x + 5 = 17' or 'sqrt(144) + 3^2'.",
                    }
                },
                "required": ["expression"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the web for current information, news, or facts Mist doesn't already know.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The search query."}
                },
                "required": ["query"],
            },
        },
    },
]

_DISPATCH = {
    "get_weather": lambda args: weather_service.get_weather(args["location"]),
    "solve_math": lambda args: math_service.solve_math(args["expression"]),
    "web_search": lambda args: search_service.web_search(args["query"]),
}


def _build_system_prompt(personality, user_profile, knowledge_base, rolling_summary, emotional_state) -> str:
    style = personality.get("speaking_style", {})
    lines = [
        f"You are {personality.get('name', 'Mist')}, a voice-first AI companion.",
        f"Tone: {personality.get('tone', '')}",
        f"Traits: {', '.join(personality.get('traits', []))}",
        f"Speaking style: {style.get('sentence_length', '')}. Avoid: {', '.join(style.get('avoids', []))}.",
        "Your replies are spoken aloud by text-to-speech — write naturally, like spoken "
        "conversation. No markdown, no bullet points, no headers, no asterisks.",
    ]

    display_name = user_profile.get("preferred_name") or user_profile.get("name")
    if display_name:
        lines.append(f"The user's name is {display_name}.")
    if user_profile.get("location"):
        lines.append(f"The user is located in {user_profile['location']}.")
    if rolling_summary:
        lines.append(f"Summary of the conversation so far: {rolling_summary}")

    current_emotion = emotional_state.get("current_emotion")
    if current_emotion and current_emotion != "neutral":
        lines.append(f"The user currently seems {current_emotion} — keep that in mind in your tone.")

    facts = knowledge_base.get("facts", [])
    if facts:
        facts_str = "; ".join(f.get("content", str(f)) if isinstance(f, dict) else str(f) for f in facts[:10])
        lines.append(f"Known facts you can draw on: {facts_str}")

    lines.append(
        "You have tools for weather, math, and web search — use them for anything needing "
        "current or precise data instead of guessing."
    )
    return "\n".join(lines)


def handle_message(user_message: str, session_id: str | None = None) -> dict:
    personality = read_json(PERSONALITY_PATH)
    user_profile = read_json(USER_PROFILE_PATH)
    conversation = read_json(CONVERSATION_PATH)
    knowledge_base = read_json(KNOWLEDGE_PATH)
    emotional_state = read_json(EMOTIONAL_STATE_PATH)

    now = datetime.now(timezone.utc).isoformat()

    # 1. Emotion detection — read the user's tone before responding.
    emotion_reading = emotion_service.detect_emotion(user_message)
    emotional_state.update(
        current_emotion=emotion_reading["emotion"],
        confidence=emotion_reading["confidence"],
        valence=emotion_reading["valence"],
        arousal=emotion_reading["arousal"],
        last_updated=now,
    )
    history = emotional_state.setdefault("history", [])
    history.append({**emotion_reading, "timestamp": now})
    emotional_state["history"] = history[-emotional_state.get("max_history", 20):]
    write_json(EMOTIONAL_STATE_PATH, emotional_state)

    # 2. Build the conversation for Groq.
    system_prompt = _build_system_prompt(
        personality, user_profile, knowledge_base, conversation.get("rolling_summary", ""), emotional_state
    )
    messages = [{"role": "system", "content": system_prompt}]
    for turn in conversation.get("recent_turns", []):
        messages.append({"role": turn["role"], "content": turn["content"]})
    messages.append({"role": "user", "content": user_message})

    # 3. Let Groq decide whether it needs a tool, loop until it settles on a reply.
    reply = "Sorry, I got a bit tangled trying to work that out."
    for _ in range(MAX_TOOL_ITERATIONS):
        message = groq_service.chat(messages, tools=TOOLS, tool_choice="auto")

        if not message.tool_calls:
            reply = message.content
            break

        messages.append(
            {
                "role": "assistant",
                "content": message.content or "",
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                    }
                    for tc in message.tool_calls
                ],
            }
        )
        for tool_call in message.tool_calls:
            fn_name = tool_call.function.name
            try:
                args = json.loads(tool_call.function.arguments)
                result = _DISPATCH[fn_name](args)
            except Exception as e:
                result = {"error": str(e)}
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": fn_name,
                    "content": json.dumps(result, default=str),
                }
            )

    # 4. Persist the turn.
    conversation.setdefault("recent_turns", []).extend(
        [
            {"role": "user", "content": user_message, "timestamp": now},
            {"role": "assistant", "content": reply, "timestamp": now},
        ]
    )
    max_turns = conversation.get("max_recent_turns", 20)
    conversation["recent_turns"] = conversation["recent_turns"][-max_turns:]
    conversation["session_id"] = session_id or conversation.get("session_id")
    conversation["last_updated"] = now
    write_json(CONVERSATION_PATH, conversation)

    return {"reply": reply, "emotion": emotion_reading}
