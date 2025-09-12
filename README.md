# Jarvis 2025

A modern AI assistant with two modes:
- Web app (Flask) for chat with LLMs (OpenAI or GitHub Models)
- Optional local desktop assistant (Eel UI, hotword detection, media/system helpers)

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

- `/` Home page
- `/login` GET/POST login form
- `/signup` GET/POST signup form
- `/chat` GET renders chat UI (requires login), POST handles chat API
	- Request JSON: `{ "message": "...", "model": "optional-model" }`
	- If no model is provided, the server uses env `OPENAI_MODEL` or `COPILOT_MODEL`.
- `/models` Returns provider info and allowed GitHub Models (when using `copilot`)
- `/admin`, `/admin/users`, `/admin/users/<id>` Admin dashboard (requires admin)
- `/logout` Clear session

Note: `/chat` POST requires a logged-in session. Use the browser UI for interactive chat.

## Using GitHub Models (Copilot) vs OpenAI

This server supports both. Select with `LLM_PROVIDER`.

- Copilot (GitHub Models):
	- Requires `GITHUB_TOKEN` (or `COPILOT_TOKEN`).
	- Endpoint is `https://models.inference.ai.azure.com` by default.
	- Optional `COPILOT_ALLOWED_MODELS=*` or a comma list to control UI model choices.
	- The server adapts `max_tokens` vs `max_completion_tokens` automatically for o3/o4 models.

- OpenAI:
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
- `pyaudio` requires PortAudio: `brew install portaudio` then `pip install pyaudio`.
- Some automation calls and the `main.py` Edge launcher are Windows-oriented (e.g., `msedge.exe`). Replace with your browser on macOS or remove that line.
- Hotword requires a Picovoice access key. Update the code or set it via env and read it in `backend/feature.py`.

Run the desktop assistant:
```bash
python run.py
```
`run.py` starts the Eel UI and the hotword listener in separate processes.

## Deployment

- Procfile (Heroku-style): `web: python app.py` (suitable for simple dynos)
- Render.com: `render.yaml` builds with `pip install -r requirements.txt` and starts `gunicorn app:app`.

### Render (recommended)
- Connect repo, pick Python environment, and import `render.yaml`.
- Set env vars: `LLM_PROVIDER`, provider keys, `SECRET_KEY`, `ADMIN_*`.
- Start command: `gunicorn app:app`.

### Vercel (serverless)
- Files added: `api/index.py`, `api/requirements.txt`, `vercel.json`.
- Vercel will deploy the Flask app as a Python serverless function.
- Configure env vars in Vercel project (same as `.env`).
- Route config in `vercel.json` sends all traffic to the function.
- Note: The serverless adapter `vercel-wsgi` is listed in `api/requirements.txt` (for Vercel only), not in root `requirements.txt` to avoid issues on other platforms.

Note: Serverless has cold starts and execution time limits; long requests may not be ideal.

### Netlify (frontend + proxy)
- File added: `netlify.toml` with redirects to a backend URL.
- Host static assets under `static/` on Netlify; set `BACKEND_URL` to your Render/Vercel backend.
- Example: `BACKEND_URL=https://your-render-app.onrender.com`.
- Note: Netlify uses root `requirements.txt` only; avoid including Vercel-only packages there.

Environment on Render:
- `PYTHON_VERSION=3.11.11`
- Choose provider variables as in the `.env` example.
- Set `ADMIN_USERNAME`/`ADMIN_PASSWORD` to avoid the default development password.

## Security Notes

- Always set a strong `SECRET_KEY` in production.
- Never commit real API keys. Use environment variables on your host.
- Do not rely on the development default admin credentials; set `ADMIN_*` env vars.

## Troubleshooting

- Missing model error on `/chat`: set `OPENAI_MODEL` or `COPILOT_MODEL`, or supply `model` in the request body.
- Copilot token issues: ensure `GITHUB_TOKEN`/`COPILOT_TOKEN` is present and has access to the chosen model.
- `pyaudio` install errors on macOS: install PortAudio via Homebrew first.
- DB mismatch: delete stray `backend/jarvis.db`; the app creates/uses `jarvis.db` at project root.

## Contributing

- Fork, create a branch, and submit a PR.
- Keep changes focused and document any new env vars or scripts.

## Acknowledgments

- OpenAI and GitHub Models (Azure AI Inference) for LLMs
- Picovoice Porcupine for hotword detection
- Everyone who contributes and tests