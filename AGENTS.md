# AGENTS.md

Arietta is a small Flask GitHub App bot. GitHub delivers `issue_comment` webhooks; a whitelisted user writes `arietta add label bug` or `arietta add milestone v1.0` and the bot applies the change plus a 👍/👎 reaction on the comment. No database, frontend, or background workers.

## Layout

- `src/arietta/app.py` — Flask app, `/webhook` route, command parsing, and `main()`.
- `src/arietta/core/auth.py` — webhook HMAC verification, JWT generation, installation-token exchange.
- `src/arietta/core/action.py` — GitHub REST calls for reactions, labels, milestones.
- `src/arietta/__main__.py` — lets `python -m arietta` run the app; `pyproject.toml` also exposes an `arietta` console script (both call `arietta.app:main`).
- `src/arietta/arietta.json` — sample config only; nothing in the code reads it.

## Run and dependencies

- Install with `uv sync` (this repo has `uv.lock`) or `pip install -r requirements.txt`.
- Two dependency sources can drift: `requirements.txt` pins Flask 3.0.3 / PyGithub 2.3.0 and lists `pyjwt`; `pyproject.toml` leaves them unpinned and omits `pyjwt` (PyGithub pulls `pyjwt[crypto]` transitively). Update both when changing deps.
- Run from the repo root: `uv run python -m arietta` (or `arietta` after an editable install). `python src/arietta/app.py` fails because the code imports `arietta.core.*` and `src` is not on the path.
- Config is environment-only, read at import time in `app.py`: `GITHUB_APP_ID`, `GITHUB_PRIVATE_KEY_PATH`, `GITHUB_WEBHOOK_SECRET`, `PORT`. Nothing loads `.env` (no python-dotenv); export the variables yourself. `.env-example` documents them and sets `PORT=5050` for local smee use.
- The dev server is `app.run(port=PORT, debug=True)` (Flask default 5000 when `PORT` is unset).

## Docker

- `docker compose up --build` publishes `5000:5000` and runs a `smee` sidecar forwarding `${SMEE_URL}` to `http://arietta-bot:5000/webhook`. `docker-compose-smee.yml` is the host-networked alternative that targets port 5050.
- `Dockerfile` installs `requirements.txt` and copies the tree into `/app`, but its command is `gunicorn app:app` while the app lives at `src/arietta/app.py` and is not installed into the image. Verify or fix that path before relying on the container.

## Behavior gotchas

- Only `issue_comment` events with `action == "created"` are handled, and the sender is checked against the hardcoded `WHITELIST = {"tvillega"}` in `app.py`.
- Known bug: `webhook()` calls `try_catch_action(..., "add tag", ...)` for label commands, but `try_catch_action()` compares against `"add label"`. The label branch never runs, so label commands always return failure (👎).
- `verify_github_signature()` reads Flask's global `request` and the raw body, so it must be called inside a request context.

## Tests

None exist, and there is no CI, linter, or formatter config in the repo. Don't invent test/lint commands; add config if you introduce tooling.

## Generated graph

`graphify-out/` contains a generated knowledge graph (`graph.json`, `GRAPH_REPORT.md`, `graph.html`). Prefer `graphify query "<question>"` over re-scanning when answering architecture questions. It is untracked — add it to `.gitignore` if it should not be committed.
