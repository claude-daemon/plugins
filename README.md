# claude-daemon plugins

Modular plugin ecosystem for [claude-daemon](https://github.com/claude-daemon/daemon).

Each plugin is independent — install one, some, or all. Cloud-first: no local model deps.

## Available plugins

| Plugin | Description | Providers |
|--------|-------------|-----------|
| [stt-whisper](stt-whisper/) | Speech-to-text for voice messages | Groq, Gemini 2.5 Flash |

## Plugin contract

Each plugin is a standalone HTTP server:

- `GET /health` → `{"status": "ok", "providers": [...]}`
- Plugin-specific endpoints (see each README)
- Configurable via env vars
- Dockerfile included

## Run any plugin

```bash
cd stt-whisper
docker build -t stt-whisper .
docker run -e GROQ_API_KEY=... -p 8765:8765 stt-whisper
```

## Contributing

Open a PR with your plugin in its own directory. Include: `main.py`, `Dockerfile`, `README.md`, `requirements.txt`.
