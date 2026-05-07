# stt-whisper

STT plugin for claude-daemon. Transcribes audio via Groq or Gemini 2.5 Flash.

## Setup

Set at least one:
```
GROQ_API_KEY=...
GOOGLE_API_KEY=...
```

Priority: Groq → Gemini. If Groq fails, falls back to Gemini.

## Run

```bash
docker build -t stt-whisper .
docker run -e GROQ_API_KEY=... -p 8765:8765 stt-whisper
```

## API

```
POST /transcribe
{"audio_b64": "<base64>", "mime_type": "audio/ogg", "lang": "es"}
→ {"transcript": "...", "provider": "groq|gemini", "duration_ms": 1200}

GET /health
→ {"status": "ok", "providers": ["groq", "gemini"]}
```
