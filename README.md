# mist_chatbot

A new Flutter project.

## Getting Started

This project is a starting point for a Flutter application.

A few resources to get you started if this is your first Flutter project:

- [Lab: Write your first Flutter app](https://docs.flutter.dev/get-started/codelab)
- [Cookbook: Useful Flutter samples](https://docs.flutter.dev/cookbook)

For help getting started with Flutter development, view the
[online documentation](https://docs.flutter.dev/), which offers tutorials,
samples, guidance on mobile development, and a full API reference.


Mist Backen readme file:

# Mist Core — Backend (v0.1)

FastAPI backend powering Mist. Tested end-to-end in this build (emotion
detection → tool-calling loop → JSON persistence → response) with Groq
mocked out; the math and route wiring were verified against real code
paths, not just import checks.

## 1. Setup

```bash
cd mist_backend
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

Open `.env` and paste in your real `GROQ_API_KEY` and `TAVILY_API_KEY`.

## 2. Run

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Visit `http://localhost:8000/docs` for interactive API docs (FastAPI's
built-in Swagger UI) — good for testing `/chat` by hand before wiring up
the frontend.

## 3. What's here

```
app/
  main.py                    # FastAPI app, CORS, /health
  config.py                  # loads .env into settings
  routes/chat.py             # POST /chat — the one endpoint the frontend calls
  core/mist_core.py          # orchestrator: emotion → LLM+tools loop → memory
  services/
    groq_service.py          # Groq client wrapper (model: openai/gpt-oss-120b)
    emotion_service.py       # emotion detection via Groq, JSON-structured output
    math_service.py          # exact math via sympy (not the LLM — precision matters)
    weather_service.py       # Open-Meteo, free, no key required
    search_service.py        # Tavily web search
  storage/json_store.py      # thread-safe atomic read/write for the JSON files
  data/                      # the five JSON files, seeded and ready
    personality.json
    user_profile.json
    conversation_knowledge.json
    knowledge_base.json
    emotional_state.json
```

## 4. How a message flows through Mist Core

1. `POST /chat` receives `{ "message": "...", "session_id": "..." }`.
2. Emotion is detected first (Groq, structured JSON output) and written to `emotional_state.json`.
3. A system prompt is built from `personality.json` + `user_profile.json` + the rolling conversation summary + current emotion + relevant facts from `knowledge_base.json`.
4. That prompt, recent conversation turns, and the new message go to Groq **with tools attached** (`get_weather`, `solve_math`, `web_search`). Groq decides on its own whether it needs one.
5. If it calls a tool, the result is fed back in and Groq is called again (looped up to 3 times) until it produces a final spoken-style reply.
6. The turn is appended to `conversation_knowledge.json` (capped at the last 20 turns — see note below).
7. Response returned: `{ "reply": "...", "emotion": {...} }`.

## 5. Connecting the Flutter frontend

In `mist_home_screen.dart`, replace the placeholder inside `_handleUtterance()`:

```dart
final response = await http.post(
  Uri.parse('http://192.168.1.135:8000/chat'),
  headers: {'Content-Type': 'application/json'},
  body: jsonEncode({'message': text, 'session_id': 'default'}),
);
final reply = jsonDecode(response.body)['reply'];
```

(Add the `http` package to `pubspec.yaml` first.) During local dev on a
physical phone, `localhost` won't reach your laptop — use your machine's
LAN IP instead, or a tunnel like ngrok.

## 6. Known v0.1 limitations, worth knowing about before you scale this

- **No conversation summarization yet.** `conversation_knowledge.json` just
  truncates to the last 20 turns rather than summarizing older ones into
  `rolling_summary`. Fine for now; once conversations run long you'll want
  a background step that condenses old turns into that summary field.
- **No automatic user-profile learning.** `user_profile.json` doesn't
  currently update itself from conversation (e.g. auto-detecting the
  user's name). Right now it's just a place Mist reads from — you'd add
  extraction logic as a next step.
- **Single global session.** All five JSON files are shared, single-user
  files, not per-user records. Fine for one person's personal Mist;
  would need a real database (and per-user file/row scoping) to support
  multiple users.
- **CORS is wide open (`*`)** for easy local development. Restrict this
  before putting the backend anywhere public.

