from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import chat

app = FastAPI(title="Mist Core", version="0.1.0")

# Allow the Flutter app to call this from any origin during development.
# Tighten this once you know your deployment setup.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router)


@app.get("/health")
def health():
    return {"status": "ok"}
