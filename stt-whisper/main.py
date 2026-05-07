# CONSULT_DONE
"""
stt-whisper — STT plugin for claude-daemon.
Groq or Gemini 2.5 Flash. Set GROQ_API_KEY, GOOGLE_API_KEY, or both.
"""

import base64
import os
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="stt-whisper", version="0.1.0")

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")
MAX_AUDIO_MB = int(os.environ.get("STT_MAX_MB", 24))
TIMEOUT_SEC = int(os.environ.get("STT_TIMEOUT", 15))
_pool = ThreadPoolExecutor(max_workers=2)


class TranscribeRequest(BaseModel):
    audio_b64: str
    mime_type: str = "audio/ogg"
    lang: str = "es"


def _transcribe_groq(audio_bytes: bytes, mime_type: str, lang: str) -> str:
    from groq import Groq
    client = Groq(api_key=GROQ_API_KEY)
    result = client.audio.transcriptions.create(
        file=("audio.ogg", audio_bytes, mime_type),
        model="whisper-large-v3-turbo",
        language=lang,
        response_format="text",
    )
    return result.text if hasattr(result, "text") else str(result)


def _transcribe_gemini(audio_bytes: bytes, mime_type: str, lang: str) -> str:
    from google import genai
    client = genai.Client(api_key=GOOGLE_API_KEY)
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[{
            "role": "user",
            "parts": [
                {"inline_data": {"mime_type": mime_type, "data": base64.b64encode(audio_bytes).decode()}},
                {"text": f"Transcribe this audio exactly as spoken. Language: {lang}. Output ONLY the transcription. If inaudible: [inaudible]"}
            ]
        }]
    )
    return response.text or ""


@app.get("/health")
def health():
    providers = []
    if GROQ_API_KEY:
        providers.append("groq")
    if GOOGLE_API_KEY:
        providers.append("gemini")
    return {"status": "ok" if providers else "no_providers", "providers": providers}


def _run_with_timeout(fn, *args) -> str:
    future = _pool.submit(fn, *args)
    try:
        return future.result(timeout=TIMEOUT_SEC)
    except TimeoutError:
        raise HTTPException(status_code=504, detail=f"Transcription timed out after {TIMEOUT_SEC}s")


@app.post("/transcribe")
def transcribe(req: TranscribeRequest):
    audio_bytes = base64.b64decode(req.audio_b64)
    size_mb = len(audio_bytes) / (1024 * 1024)
    if size_mb > MAX_AUDIO_MB:
        raise HTTPException(status_code=413, detail=f"Audio too large: {size_mb:.1f}MB (max {MAX_AUDIO_MB}MB)")

    t0 = time.monotonic()

    if GROQ_API_KEY:
        try:
            transcript = _run_with_timeout(_transcribe_groq, audio_bytes, req.mime_type, req.lang)
            return {"transcript": transcript, "provider": "groq", "duration_ms": int((time.monotonic() - t0) * 1000)}
        except HTTPException:
            raise
        except Exception as e:
            if not GOOGLE_API_KEY:
                raise HTTPException(status_code=502, detail=f"Groq failed: {e}")

    if GOOGLE_API_KEY:
        try:
            transcript = _run_with_timeout(_transcribe_gemini, audio_bytes, req.mime_type, req.lang)
            return {"transcript": transcript, "provider": "gemini", "duration_ms": int((time.monotonic() - t0) * 1000)}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Gemini failed: {e}")

    raise HTTPException(status_code=503, detail="No provider configured. Set GROQ_API_KEY or GOOGLE_API_KEY.")


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("STT_PORT", 8765))
    uvicorn.run(app, host="0.0.0.0", port=port)
