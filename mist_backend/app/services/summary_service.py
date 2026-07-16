from app.services import groq_service

_SYSTEM_PROMPT = """You maintain a running summary of an ongoing conversation between a user \
and their AI companion, Mist. You'll be given the existing summary (may be empty) and a batch \
of older conversation turns that are about to be dropped from raw memory. Produce an updated \
summary that folds in anything worth remembering long-term — key facts, decisions, context, \
recurring topics — and drops small talk and pleasantries. Keep it tight: a few sentences, not \
a transcript. Respond with ONLY the updated summary text, no preamble, no labels."""


def update_summary(existing_summary: str, turns_to_fold_in: list[dict]) -> str:
    transcript = "\n".join(f"{t['role']}: {t['content']}" for t in turns_to_fold_in)
    user_content = (
        f"Existing summary:\n{existing_summary or '(none yet)'}\n\n"
        f"Older turns to fold in and then forget:\n{transcript}"
    )
    message = groq_service.chat(
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        temperature=0.3,
    )
    return (message.content or existing_summary).strip()
