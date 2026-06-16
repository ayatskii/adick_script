"""FastAPI backend for the Edvibe Grader web app.

Connects the React frontend (web/) to the bot core (edvibe_bot/) via REST + WS.
Read-only against the bot-core SQLite store; runs are driven through
``edvibe_bot.runner.run`` on a worker thread (see ``jobs.RunManager``).
"""
