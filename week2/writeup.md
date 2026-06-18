# Week 2 Write-up
Tip: To preview this markdown file
- On Mac, press `Command (⌘) + Shift + V`
- On Windows/Linux, press `Ctrl + Shift + V`

## INSTRUCTIONS

Fill out all of the `TODO`s in this file.

## SUBMISSION DETAILS

Name: **TODO** \
SUNet ID: **TODO** \
Citations: Claude Code (Anthropic) was used as an AI assistant throughout this assignment to implement, test, and refactor the codebase.

This assignment took me about **3** hours to do. 


## YOUR RESPONSES
For each exercise, please include what prompts you used to generate the answer, in addition to the location of the generated response. Make sure to clearly add comments in your code documenting which parts are generated.

### Exercise 1: Scaffold a New Feature
Prompt: 
```
Help me implement TODO 1 from the assignment: implement extract_action_items_llm()
that uses Ollama with structured outputs (JSON array of strings) to extract action
items from free-form text. Use Pydantic for output validation instead of raw JSON schema.
The available model on this machine is llama3.1:8b.
``` 

Generated Code Snippets:
```
week2/app/services/extract.py
  - Line 13-14: OLLAMA_MODEL constant (configurable via env var)
  - Line 17-18: ActionItemsOutput Pydantic model for structured LLM output
  - Line 76-100: extract_action_items_llm() function — calls ollama.chat() with
                  ActionItemsOutput.model_json_schema() as format, parses response
                  with model_validate_json()
```

### Exercise 2: Add Unit Tests
Prompt: 
```
/tdd Write unit tests for extract_action_items_llm() covering multiple inputs
(e.g., bullet lists, keyword-prefixed lines, empty input) in week2/tests/test_extract.py.
Use mocking for the Ollama chat call so tests run offline.
``` 

Generated Code Snippets:
```
week2/tests/test_extract.py
  - Line 35-40:  test_llm_empty_input_returns_empty_list — verifies no LLM call on empty input
  - Line 42-47:  test_llm_whitespace_only_returns_empty_list — same for whitespace-only input
  - Line 49-56:  test_llm_free_form_text_extracts_action_items — LLM extracts from prose
  - Line 58-65:  test_llm_bullet_list_extracts_items — LLM extracts from bullet list
  - Line 67-74:  test_llm_keyword_prefixed_lines_extracts_items — LLM extracts todo:/action: lines
  - Line 76-79:  test_llm_no_action_items_returns_empty_list — LLM returns [] when nothing found
```

### Exercise 3: Refactor Existing Code for Clarity
Prompt: 
```
/tdd Refactor the backend for clarity: add well-defined Pydantic request/response schemas
to both routers (replacing Dict[str, Any]), move init_db() into a FastAPI lifespan context
manager instead of calling it at module import time, add a 404 response for mark_done when
the action item doesn't exist, and write API integration tests as a safety net before
refactoring.
``` 

Generated/Modified Code Snippets:
```
week2/app/routers/notes.py (full rewrite)
  - Line 13-20: NoteCreate and NoteResponse Pydantic schemas
  - Line 23-27: list_notes() — new GET /notes endpoint (added in TODO 4)
  - Line 29-33: create_note() — uses NoteCreate input, returns NoteResponse
  - Line 38-42: get_single_note() — returns NoteResponse, raises 404 if not found

week2/app/routers/action_items.py (full rewrite)
  - Line 14-43: Pydantic schemas: ExtractRequest, ActionItemResponse, ExtractResponse,
                ActionItemListItem, MarkDoneRequest, MarkDoneResponse
  - Line 46-60: extract() — POST /action-items/extract using heuristic extraction
  - Line 80-89: list_all() — GET /action-items with optional note_id query param
  - Line 95-100: mark_done() — raises 404 if action item not found

week2/app/main.py
  - Line 15-17: lifespan() async context manager — init_db() moved here from module level

week2/app/db.py
  - Line 107-115: get_action_item() — new function to look up a single action item by ID

week2/tests/test_api.py (new file)
  - Line 21-27: client fixture — monkeypatches DB_PATH to tmp_path, uses TestClient as
                context manager to trigger lifespan
  - Line 31-116: 10 API integration tests covering notes and action-items endpoints
```


### Exercise 4: Use Agentic Mode to Automate a Small Task
Prompt: 
```
/tdd Add a new POST /action-items/extract-llm endpoint using extract_action_items_llm(),
keeping the existing POST /action-items/extract as heuristic-only. Also add GET /notes to
list all saved notes. Update the frontend to include an "Extract LLM" button that calls
the new endpoint and a "List Notes" button that fetches and displays all notes.
``` 

Generated Code Snippets:
```
week2/app/routers/action_items.py
  - Line 63-78: extract_llm() — new POST /action-items/extract-llm endpoint using
                extract_action_items_llm()

week2/app/routers/notes.py
  - Line 23-27: list_notes() — new GET /notes endpoint returning all saved notes

week2/frontend/index.html
  - Line 34:    "Extract LLM" button wired to /action-items/extract-llm
  - Line 38:    "List Notes" button
  - Line 51-61: doExtract() shared handler called by both extract buttons
  - Line 63-64: event listeners for Extract (heuristic) and Extract LLM buttons
  - Line 66-80: List Notes click handler — fetches GET /notes and renders results

week2/tests/test_api.py
  - Line 81-95:  test_extract_llm_returns_items and test_extract_llm_empty_text_returns_400
  - Line 97-105: test_list_notes_returns_list
```


### Exercise 5: Generate a README from the Codebase
Prompt: 
```
Analyze the current codebase and generate a well-structured README.md for the week2
project. Include: a brief project overview, setup and run instructions (Poetry + Ollama),
all API endpoints with method/path/description in a table, request body examples, and
instructions for running the test suite.
``` 

Generated Code Snippets:
```
week2/README.md (new file)
  - Overview section: describes heuristic vs LLM extraction and SQLite persistence
  - Setup section: prerequisites, poetry install, ollama pull, OLLAMA_MODEL env var
  - Running section: uvicorn command and browser URL
  - API Endpoints section: tables for /notes and /action-items with request body examples
  - Running tests section: pytest commands for individual test files
```


## SUBMISSION INSTRUCTIONS
1. Hit a `Command (⌘) + F` (or `Ctrl + F`) to find any remaining `TODO`s in this file. If no results are found, congratulations – you've completed all required fields. 
2. Make sure you have all changes pushed to your remote repository for grading.
3. Submit via Gradescope.
