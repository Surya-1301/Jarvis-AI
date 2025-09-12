# Jarvis 2025

A modern AI assistant with two modes:

This README reflects the current codebase layout and how to run both modes.

## Quick Start (Web App)

Prerequisites: Python 3.10+ recommended (Render uses 3.11), `pip`, and an API key for either OpenAI or GitHub Models.

1) Create a virtual environment and install dependencies:
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2) Create a `.env` file (choose ONE provider):
```bash
# Common
SECRET_KEY=change-me
PORT=5000

# Option A: GitHub Models via Azure AI Inference
LLM_PROVIDER=copilot
GITHUB_TOKEN=ghu_xxx   # or set COPILOT_TOKEN
COPILOT_MODEL=gpt-4o-mini
# Optional
# COPILOT_API_BASE=https://models.inference.ai.azure.com
# COPILOT_ALLOWED_MODELS=gpt-4o,gpt-4o-mini,o4-mini
# COPILOT_AUTH_SCHEME=bearer   # or api-key (some endpoints)

# Option B: OpenAI Platform
# LLM_PROVIDER=openai
# OPENAI_API_KEY=sk-...
# OPENAI_MODEL=gpt-3.5-turbo
# OPENAI_API_BASE=https://<your-endpoint>/v1  # for Azure OpenAI/proxy

# Seed an admin user on boot (optional - strongly recommended)
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your-strong-password
```

3) Run the web server:
```bash
python app.py
```
Open http://localhost:${PORT:-5000} in your browser.

Login at /login, or create an account at /signup. The admin user is created/updated from `ADMIN_USERNAME` and `ADMIN_PASSWORD` on startup.

## Endpoints

	- Request JSON: `{ "message": "...", "model": "optional-model" }`
	- If no model is provided, the server uses env `OPENAI_MODEL` or `COPILOT_MODEL`.

Note: `/chat` POST requires a logged-in session. Use the browser UI for interactive chat.

## Using GitHub Models (Copilot) vs OpenAI

This server supports both. Select with `LLM_PROVIDER`.

	- Requires `GITHUB_TOKEN` (or `COPILOT_TOKEN`).
	- Endpoint is `https://models.inference.ai.azure.com` by default.
	- Optional `COPILOT_ALLOWED_MODELS=*` or a comma list to control UI model choices.
	- The server adapts `max_tokens` vs `max_completion_tokens` automatically for o3/o4 models.

	- Requires `OPENAI_API_KEY`; optionally set `OPENAI_API_BASE` (Azure/proxy) and `OPENAI_MODEL`.

List available models (for Copilot):
```bash
curl http://localhost:${PORT:-5000}/models
```

## Project Structure

```
Jarvis-2025/
├── app.py                 # Flask web app (login, chat, admin)
├── run.py                 # Spawns local UI + hotword processes (desktop mode)
├── main.py                # Local Eel UI bootstrap (desktop mode)
├── backend/
│   ├── feature.py         # Hotword, YouTube, OpenAI/Copilot chat helper (desktop)
│   ├── command.py         # TTS/command utilities
│   ├── config.py          # Assistant name and constants
│   ├── helper.py          # Parsing helpers
│   └── auth/              # Face authentication (Eel UI)
├── templates/             # Flask templates (home, login, signup, admin)
├── static/                # Flask static assets
├── frontend/              # Eel local UI assets
├── render.yaml            # Render.com service definition (gunicorn app:app)
├── Procfile               # Heroku-style process file
├── requirements.txt       # Server dependencies
└── README.md
```

Important: The app uses an SQLite database `jarvis.db` in the project root (auto-created). If you have an older DB file under `backend/`, it will not be used by the Flask app.

## Local Desktop Assistant (Optional)

The desktop assistant uses Eel, hotword detection (Picovoice Porcupine), and OS automation. It needs extra packages that are not in `requirements.txt`.

Additional dependencies:
```bash
pip install eel pygame pvporcupine pyaudio pyautogui pywhatkit hugchat
```

macOS notes:

Run the desktop assistant:
```bash
python run.py
```
`run.py` starts the Eel UI and the hotword listener in separate processes.

## Deployment


### Render (recommended)

### Vercel (serverless)

Note: Serverless has cold starts and execution time limits; long requests may not be ideal.

### Netlify (frontend + proxy)

### Netlify-only backend (serverless)
	- File system is ephemeral; SQLite writes are not persistent between invocations. For production, use an external DB (e.g., Postgres, Supabase) and set `DB_PATH` accordingly or swap to a DB URL.
	- Function timeouts can affect long LLM calls; consider keeping Render/Vercel for backend if you see timeouts.

Environment on Render:

## Security Notes


## Troubleshooting


## Contributing


## Acknowledgments
