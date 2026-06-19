# Issue 5: README Update — Automatic OAuth Flow

## What to build

Update `week3/README.md` to reflect that Claude CLI now handles the OAuth flow automatically. Remove the manual token copy-paste instructions and replace with a single `claude mcp add` command.

**Remove from README:**
- The manual "Authentication Flow" steps (visit `/oauth/authorize`, copy JSON token, paste into config)
- The "Connecting with Claude Code CLI" section that requires `claude mcp remove` + `claude mcp add` after every server restart
- Any mention of manually managing Bearer tokens

**Add to README:**

1. **How automatic OAuth works** — brief explanation that Claude CLI discovers the auth flow via metadata endpoints, opens the browser once, and stores the token automatically.

2. **Updated "Connecting with Claude Code CLI" section:**
   ```bash
   claude mcp add --transport http weather http://localhost:8000/mcp -s project
   ```
   On first use, Claude CLI will open a browser for GitHub login automatically. No token management needed.

3. **Note about server restart** — tokens are in-memory and lost on restart. Claude CLI will re-trigger the browser flow automatically when its stored token is rejected (401). No manual steps needed.

4. **Keep MCP Inspector section** — Inspector users still need to manually copy a token (Inspector does not implement the MCP Authorization Spec). Keep those instructions intact.

## Acceptance criteria

- [ ] README no longer instructs the user to manually copy a token
- [ ] `claude mcp add` command in README does not include `--header` flag
- [ ] README explains that the browser opens automatically on first use
- [ ] MCP Inspector section is preserved with its manual token instructions
- [ ] README note clarifies token behavior on server restart (automatic re-auth, no manual steps)

## Blocked by

Issue 4 — the full automatic flow must work before the docs can accurately describe it.
