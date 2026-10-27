# Developer Support Assistant

A small web app that answers developer questions using a local ChromaDB knowledge
base and the Gemini API. Run the backend and frontend in separate terminals.

## Requirements

- Python 3.10 or later
- A Gemini API key

## Setup

From the project root, create and activate a virtual environment, then install
the backend dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
```

On Windows PowerShell, activate the environment with:

```powershell
.venv\Scripts\Activate.ps1
```

Create `backend/.env` and add your Gemini API key:

```dotenv
GEMINI_API_KEY=your_gemini_api_key
# Optional; defaults to gemini-3.8-flash
GEMINI_MODEL=gemini-3.8-flash
```

Get a key from [Google AI Studio](https://aistudio.google.com/app/apikey).
Keep the key private; do not commit or share the `.env` file.

## Run the application

In the first terminal, start the FastAPI backend from the `backend` directory:

```bash
cd backend
uvicorn main:app --reload --port 8000
```

In a second terminal, serve the frontend. From the project root, run:

```bash
python3 -m http.server 5500 --directory frontend
```

If your terminal is already in `backend/`, use:

```bash
python3 -m http.server 5500 --directory ../frontend
```

If your terminal is already in `frontend/`, serve the current directory:

```bash
python3 -m http.server 5500
```

Open [http://localhost:5500](http://localhost:5500) in your browser. The frontend
sends requests to the backend at `http://localhost:8000`. While Gemini works,
the page shows the current stage and streams answer text as it is generated.

The first backend startup seeds the local ChromaDB knowledge base. The database
is stored under `backend/chroma_db/`.

## Troubleshooting

- **`API_KEY_INVALID`**: Check that `backend/.env` contains a valid, active
  `GEMINI_API_KEY`. If the key was shared or exposed, revoke it and create a
  replacement. Restart the backend after changing the key.
- **Gemini returns `404 NOT_FOUND` for a model**: The configured model may no
  longer be available or may not support `generateContent`. Set `GEMINI_MODEL`
  in `backend/.env` to a model available to your API key, such as
  `gemini-3.8-flash`, then restart the backend. The backend uses Google's
  Interactions API. See the [Gemini API model catalog](https://ai.google.dev/gemini-api/docs/models).
- **`OPTIONS` returns `501 Unsupported method`**: Port 8000 must be running the
  FastAPI backend (`uvicorn main:app ...`), not Python's static file server.
- **Frontend URL returns `404 File not found`**: Stop the frontend server with
  `Ctrl+C` and restart it using the command that matches your current directory.
  The served directory must contain `index.html`; from `frontend/`, run
  `python3 -m http.server 5500` without `--directory frontend`.
- **Frontend cannot connect**: Keep both servers running in separate terminals
  and open the frontend at `http://localhost:5500`.