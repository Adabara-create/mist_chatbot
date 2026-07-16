from fastapi import APIRouter, HTTPException

from app.core import mist_core
from app.models.schemas import ChatRequest, ChatResponse

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="message cannot be empty")

    result = mist_core.handle_message(request.message, request.session_id)
    return ChatResponse(reply=result["reply"], emotion=result["emotion"])
