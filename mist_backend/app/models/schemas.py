from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None


class EmotionReading(BaseModel):
    emotion: str
    confidence: float
    valence: float
    arousal: float


class ChatResponse(BaseModel):
    reply: str
    emotion: EmotionReading
