# Quiz Bot

Small quiz bot project.

Files:
- `bot.py` - entrypoint placeholder
- `config.py` - configuration values loaded from environment
- `requirements.txt` - Python dependencies
- `.env` - environment variables for local development
- `src/` - source folders (handlers, services, database, utils, constants)
- `data/` - data storage (questions, database)
- `tests/` - tests

To run (create a venv first):

```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1; pip install -r requirements.txt
python bot.py
```

Replace BOT_TOKEN in `.env` before using a real bot.