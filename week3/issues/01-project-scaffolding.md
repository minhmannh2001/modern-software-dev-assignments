# Issue 1: Project Scaffolding

## What to build

Set up the complete skeleton for the week3 MCP server so every subsequent issue has a working foundation to build on. This includes the directory layout, dependency management, environment variable config, and a smoke-testable entrypoint.

Directory layout:
```
week3/
├── server/
│   ├── main.py          # entrypoint (stub)
│   ├── config.py        # env var loading
│   ├── auth.py          # stub
│   └── tools/
│       ├── __init__.py
│       └── weather.py   # stub
├── .env.example
├── requirements.txt
└── README.md            # placeholder
```

`config.py` must load and validate: `GITHUB_CLIENT_ID`, `GITHUB_CLIENT_SECRET`, `REDIRECT_URI`, `PORT` (default `8000`). Fail fast with a clear error if required vars are missing.

`.env.example` lists every variable with a comment explaining each one.

## Acceptance criteria

- [ ] `week3/server/` directory exists with the module structure above
- [ ] `requirements.txt` includes `mcp[cli]`, `httpx`, `python-dotenv`, `starlette`, `uvicorn`
- [ ] `config.py` raises a descriptive error on startup if `GITHUB_CLIENT_ID` or `GITHUB_CLIENT_SECRET` is missing
- [ ] `.env.example` documents all required and optional env vars
- [ ] Running `uvicorn server.main:app` from `week3/` starts without import errors (stubs are fine)

## Blocked by

None — can start immediately.
