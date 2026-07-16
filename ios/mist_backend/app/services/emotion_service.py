from app.services import groq_service

_SYSTEM_PROMPT = """You are an emotion-detection engine. Read the user's message and \
classify their emotional tone. Respond ONLY with a JSON object shaped exactly like this, \
no extra keys, no commentary:

{
  "emotion": "one short word, e.g. happy, sad, anxious, excited, frustrated, neutral, curious",
  "confidence": 0.0 to 1.0,
  "valence": -1.0 to 1.0 (negative = unpleasant, positive = pleasant),
  "arousal": 0.0 to 1.0 (0 = calm/low energy, 1 = intense/high energy)
}"""


def detect_emotion(user_message: str) -> dict:
    result = groq_service.chat_json(
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ]
    )
    # Defensive defaults in case the model omits a field.
    return {
        "emotion": result.get("emotion", "neutral"),
        "confidence": float(result.get("confidence", 0.5)),
        "valence": float(result.get("valence", 0.0)),
        "arousal": float(result.get("arousal", 0.3)),
    }
