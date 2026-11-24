# Autonomous enterprise AI agent

A local demonstration of an AI assistant that performs inventory lookups, CRM
lead updates, and support-ticket creation through mock REST APIs. It includes a
Streamlit interface, a FastAPI backend, SQLite persistence, input validation,
retries for transient API failures, and explicit human approval before writes.

## Requirements

- Python 3.10 or later
- A terminal opened in this project folder
- Optional: an OpenAI API key for LLM-based function selection. Without a key,
  the app uses its built-in local intent planner.

## Install

PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

The `.env` file is ignored by git. To enable OpenAI planning, add:

```dotenv
OPENAI_API_KEY=your-key
OPENAI_MODEL=gpt-4o-mini
```

No key is required to use the local planner.

## Run

Start the mock API in the first terminal:

```powershell
.\.venv\Scripts\Activate.ps1
uvicorn api.main:app --reload
```

Start the Streamlit interface in a second terminal:

```powershell
.\.venv\Scripts\Activate.ps1
streamlit run app.py
```

Open the Streamlit URL printed in the second terminal (normally
`http://localhost:8501`). The API is available at `http://127.0.0.1:8000` and
its interactive documentation at `http://127.0.0.1:8000/docs`.

The UI's **Mock API address** setting and the `API_BASE_URL` environment
variable can be used to point the frontend at another API instance.

## Try it

- `Check stock for laptop`
- `Check inventory for P104`
- `Update lead L101 to Contacted`
- `Create a ticket for Rahul about a payment issue`

Inventory lookup runs immediately. Lead changes and ticket creation are shown
in an approval panel first; the API write is not sent until **Approve and
execute** is selected. Declining an operation leaves business data unchanged.
The execution-history tab keeps a per-browser-session action log.

## Mock API

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/health` | API status |
| `GET` | `/inventory?search=laptop` | Search products by name or ID |
| `GET` | `/leads` | List CRM leads |
| `PATCH` | `/leads/{lead_id}` | Update a lead to an allowed status |
| `GET` | `/tickets` | List support tickets |
| `POST` | `/tickets` | Create a support ticket |

SQLite data is stored in `enterprise.db` in the project directory by default.
Set `DATABASE_PATH` to use a different local database file. The API seeds
sample inventory and leads the first time it starts.

## Tests

```powershell
python -m pytest
```