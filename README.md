# FitBuddy – AI Fitness Plan Generator (Gemini + FastAPI)

FitBuddy generates a personalized **7-day workout plan** and a matching
**nutrition/recovery tip** from a short user profile, lets users **submit
feedback** to revise their plan, and gives admins a **dashboard** of all
users and plans.

- **Backend:** FastAPI
- **AI:** Google Gemini, via the current `google-genai` SDK
  (Pro-tier model for the workout plan & feedback revisions, Flash-tier
  model for the quick nutrition tip)
- **Database:** SQLite via SQLAlchemy
- **Frontend:** Jinja2 templates + embedded CSS (no build step needed)

> **Note on the AI SDK:** the original project spec references the
> `google-generativeai` package. Google has since deprecated that
> package in favor of a new, unified `google-genai` SDK, so this build
> uses `google-genai` instead — the usage pattern is nearly identical.
> If your Gemini model names differ from the defaults below, just change
> them in `.env` (no code changes needed).

---

## 1. Project structure

```
fitbuddy/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI app entrypoint
│   ├── routes.py                  # All page/API routes
│   ├── database.py                # SQLAlchemy models + DB helper functions
│   ├── models.py                  # Pydantic schemas (UserInput, FeedbackRequest)
│   ├── ai_client.py                # Shared Gemini client factory
│   ├── gemini_generator.py        # generate_workout_gemini() – Gemini Pro
│   ├── gemini_flash_generator.py  # generate_nutrition_tip_with_flash() – Gemini Flash
│   └── updated_plan.py            # update_workout_plan() – feedback-based revision
├── templates/
│   ├── index.html                 # Input form
│   ├── result.html                # Plan + tip + feedback form
│   └── all_users.html             # Admin dashboard
├── static/
│   ├── css/style.css              # Optional shared styles (templates are self-styled)
│   └── images/
├── tests/
│   └── test_app.py                # Pytest smoke tests (Gemini calls mocked)
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

## 2. Prerequisites

- **Python 3.10+** (uses modern type-hint syntax like `str | None`)
- A free **Gemini API key** from [Google AI Studio](https://aistudio.google.com/app/apikey)
- **VS Code** with the official **Python extension** (ms-python.python)

---

## 3. VS Code setup

1. **Open the folder:** `File → Open Folder...` → select the `fitbuddy/` folder.
2. **Create a virtual environment:**
   Open the integrated terminal (`` Ctrl+` ``/`` Cmd+` ``) and run:

   ```bash
   python -m venv venv
   ```

   - Windows: `venv\Scripts\activate`
   - macOS/Linux: `source venv/bin/activate`

3. **Select the interpreter:** `Ctrl/Cmd+Shift+P` → *Python: Select Interpreter* →
   choose the `venv` interpreter (VS Code usually detects it automatically
   and offers to select it).
4. **Install dependencies** (see step 4 below) inside that terminal.

---

## 4. Installation

From the `fitbuddy/` root, with your virtual environment activated:

```bash
pip install -r requirements.txt
```

Then set up your environment variables:

```bash
# macOS/Linux
cp .env.example .env

# Windows (PowerShell)
copy .env.example .env
```

Open `.env` and paste in your real key:

```
GOOGLE_API_KEY=your_gemini_api_key_here
```

(The `GEMINI_PRO_MODEL` / `GEMINI_FLASH_MODEL` lines are optional — only
change them if Google renames or retires the default model names.)

---

## 5. Running the app

```bash
uvicorn app.main:app --reload
```

- App: <http://127.0.0.1:8000>
- Interactive API docs (Swagger UI): <http://127.0.0.1:8000/docs>
- Admin dashboard: <http://127.0.0.1:8000/view-all-users>

The SQLite database file (`fitbuddy.db`) is created automatically in the
project root on first run — no manual migration step needed.

**In VS Code:** you can also just press `F5` (or use the "Run and Debug"
panel) after adding a launch config, or simply run the command above in
the integrated terminal — both work fine for local development.

---

## 6. Using the app

1. Go to `/` and fill in your name, user ID, age, weight, fitness goal,
   and workout intensity → **Generate Plan**.
2. Review your 7-day workout plan and nutrition tip on the result page.
3. Optionally submit **feedback** (e.g. *"add more cardio"*, *"include
   more rest days"*) to get a revised plan — both the original and
   updated plans are kept.
4. Visit `/view-all-users` to see every user and their plan(s) in one
   dashboard (with a delete option per user).

---

## 7. Testing

Automated tests mock the Gemini calls, so they run instantly and **do
not require a real API key or internet access**:

```bash
pip install pytest httpx   # if not already installed
pytest -v
```

Manual verification checklist:

- [ ] `GET /` loads the form and renders without errors
- [ ] Submitting the form on `/` returns a 7-day plan + nutrition tip
- [ ] Submitting feedback on the result page returns a revised plan
- [ ] `/view-all-users` lists the users you created, with correct data
- [ ] `/docs` shows all four routes and lets you try them interactively
- [ ] Restarting the server preserves data (SQLite persists to `fitbuddy.db`)

---

## 8. Troubleshooting

| Issue | Fix |
|---|---|
| `RuntimeError: GOOGLE_API_KEY is not set` | Make sure `.env` exists (copied from `.env.example`) and contains a real key, and that you started the server from the project root. |
| `404 model not found` from Gemini | The default model name may have changed. Update `GEMINI_PRO_MODEL` / `GEMINI_FLASH_MODEL` in `.env` to a currently supported model from [Google's model list](https://ai.google.dev/gemini-api/docs/models). |
| `ModuleNotFoundError` on startup | Confirm your virtual environment is activated and `pip install -r requirements.txt` completed without errors. |
| Port already in use | Run on a different port: `uvicorn app.main:app --reload --port 8001` |
