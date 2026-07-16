import json
import random
from datetime import datetime, timezone

from app.config import settings
from app.storage.json_store import read_json, write_json
from app.services import groq_service, math_service, weather_service, search_service, emotion_service, profile_service, summary_service

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

_OPENER_CATEGORY_BY_EMOTION = {
    "happy": "excited", "excited": "excited", "joyful": "excited", "amused": "excited",
    "sad": "empathetic", "down": "empathetic", "disappointed": "empathetic",
    "anxious": "empathetic", "worried": "empathetic", "nervous": "empathetic", "stressed": "empathetic",
    "frustrated": "empathetic", "angry": "empathetic", "annoyed": "empathetic",
    "curious": "curious_or_interested", "interested": "curious_or_interested",
}


def _pick_opener_examples(personality: dict, current_emotion: str, count: int = 6) -> list[str]:
    """Pull a small, varied sample of style-reference openers relevant to the
    user's current mood — never the full list, and never the same subset
    twice in a row, so it reads as natural rather than scripted."""
    openers = personality.get("conversational_openers", {})
    category = _OPENER_CATEGORY_BY_EMOTION.get((current_emotion or "").lower(), "casual")
    pool = list(openers.get(category, [])) + list(openers.get("casual", []))
    if not pool:
        return []
    return random.sample(pool, min(count, len(pool)))


def _build_system_prompt(personality, user_profile, knowledge_base, rolling_summary, emotional_state) -> str:
    style = personality.get("speaking_style", {})
    lines = [
        f"You are {personality.get('name', 'Mist')}, an AI companion chatting with the user over text.",
        f"Tone: {personality.get('tone', '')}",
        f"Traits: {', '.join(personality.get('traits', []))}",
        f"Speaking style: {style.get('sentence_length', '')}. Avoid: {', '.join(style.get('avoids', []))}.",
        "You're chatting over text, not speaking aloud — write naturally for reading. "
        "Use paragraphs and formatting (line breaks, lists) when they genuinely help. "
        "You're fully capable of creative writing — if asked for a story, poem, or "
        "similar, write it properly with real craft, not just a summary of one.",
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

    opener_examples = _pick_opener_examples(personality, current_emotion)
    if opener_examples:
        examples_str = " / ".join(f'"{o}"' for o in opener_examples)
        lines.append(
            "Style reference for how you might open this reply, matching the moment "
            "(don't recite these verbatim, don't reuse the same one often — write your "
            "own natural variation in this spirit): " + examples_str
        )

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

    # 1b. Pull out any durable facts about the user from this message —
    # name, location, etc. — and remember them for future conversations.
    profile_updates = profile_service.extract_profile_updates(user_message)
    profile_changed = False
    for field in ("name", "preferred_name", "location", "timezone"):
        value = profile_updates.get(field)
        if value:
            user_profile[field] = value
            profile_changed = True
    recurring_facts = user_profile.setdefault("recurring_facts", [])
    for fact in profile_updates.get("new_facts", []):
        if fact and fact not in recurring_facts:
            recurring_facts.append(fact)
            profile_changed = True
    if profile_changed:
        user_profile["last_updated"] = now
        write_json(USER_PROFILE_PATH, user_profile)

    # 1c. Same extraction pass also surfaces general facts worth keeping —
    # not about the user's identity, but context worth remembering.
    kb_facts = knowledge_base.setdefault("facts", [])
    existing_contents = {f.get("content") if isinstance(f, dict) else f for f in kb_facts}
    knowledge_changed = False
    for fact in profile_updates.get("general_facts", []):
        if fact and fact not in existing_contents:
            kb_facts.append({"content": fact, "source": "conversation", "added_at": now})
            existing_contents.add(fact)
            knowledge_changed = True
    if knowledge_changed:
        write_json(KNOWLEDGE_PATH, knowledge_base)

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
    if len(conversation["recent_turns"]) > max_turns:
        overflow = len(conversation["recent_turns"]) - max_turns
        turns_to_summarize = conversation["recent_turns"][:overflow]
        conversation["recent_turns"] = conversation["recent_turns"][overflow:]
        conversation["rolling_summary"] = summary_service.update_summary(
            conversation.get("rolling_summary", ""), turns_to_summarize
        )
    conversation["session_id"] = session_id or conversation.get("session_id")
    conversation["last_updated"] = now
    write_json(CONVERSATION_PATH, conversation)

    return {"reply": reply, "emotion": emotion_reading}
