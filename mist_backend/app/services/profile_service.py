from app.services import groq_service

_SYSTEM_PROMPT = """You extract durable information from a single chat message, to be \
remembered long-term. Only include something if it is clearly and explicitly stated by the \
user in THIS message — never guess, infer, or carry over assumptions. Respond ONLY with a \
JSON object shaped exactly like this, using null/empty lists for anything not mentioned:

{
  "name": "the user's real name, or null",
  "preferred_name": "what they want to be called, if different from their name, or null",
  "location": "a city/region they mentioned about themselves, or null",
  "timezone": "a timezone they mentioned, or null",
  "new_facts": ["short standalone facts ABOUT THE USER PERSONALLY worth remembering, or an empty list"],
  "general_facts": ["short standalone facts NOT specifically about the user's identity — e.g. facts about their project, corrections they gave, general context worth remembering — or an empty list"]
}"""


def extract_profile_updates(user_message: str) -> dict:
    result = groq_service.chat_json(
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ]
    )
    return {
        "name": result.get("name"),
        "preferred_name": result.get("preferred_name"),
        "location": result.get("location"),
        "timezone": result.get("timezone"),
        "new_facts": result.get("new_facts") or [],
        "general_facts": result.get("general_facts") or [],
    }
