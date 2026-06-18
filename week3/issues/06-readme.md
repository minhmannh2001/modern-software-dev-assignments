# Issue 6: README

## What to build

Write `week3/README.md` — the complete developer guide for setting up, running, and using the MCP weather server.

**Sections required:**

1. **Overview** — what the server does, which transport and auth mechanism it uses.
2. **Prerequisites** — Python version, how to install dependencies.
3. **GitHub OAuth App setup** — step-by-step: go to github.com/settings/developers → New OAuth App → set Authorization callback URL to `http://localhost:8000/oauth/callback` → copy Client ID and Client Secret.
4. **Environment setup** — copy `.env.example` to `.env`, fill in the two GitHub values.
5. **Running the server** — single command with uvicorn, expected startup output.
6. **Authentication flow** — how to complete the OAuth dance manually (visit `/oauth/authorize` in a browser, copy the returned token).
7. **Connecting with MCP Inspector** — `npx @modelcontextprotocol/inspector`, where to paste the server URL and the Bearer token.
8. **Tool reference** — table or section per tool: name, parameters (type, description), example input, example output, error cases.
9. **Running tests** — command to run the test suite.

## Acceptance criteria

- [ ] README covers all 9 sections listed above
- [ ] GitHub OAuth App setup instructions are accurate (correct URL, correct callback URL format)
- [ ] Tool reference documents all 3 tools with parameter types and example inputs/outputs
- [ ] A developer with no prior context can follow the README and successfully call a tool via MCP Inspector

## Blocked by

Issue 5 — server must be complete before docs can be written accurately.
