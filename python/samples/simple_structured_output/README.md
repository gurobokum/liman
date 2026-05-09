# Simple Structured Output

This sample shows how to use `structured_output` in a Liman `LLMNode` to extract typed fields from free-form text.

The agent reads a book description from the user and returns a JSON object.

## How it works

The `extractor` node in `specs/extractor_llm.yaml` declares a `structured_output` map. Liman passes this as a JSON schema to the LLM via `with_structured_output`, so the response is always a typed dict instead of plain text.

## Setup

Copy `.env.example` to `.env` and fill in one API key:

```
OPENAI_API_KEY=sk-...
# or
GOOGLE_STUDIO_API_KEY=...
```

Install dependencies:

```bash
uv sync
```

## Run

```bash
python src/main.py
```

Example session:

```
Describe a book (or 'exit'): Any 19th-century murder mystery set in England.
╭─ Extracted ────────────────────────────────────────────────────────────────────────────╮
│ {'title': 'A Study in Scarlet', 'author': 'Arthur Conan Doyle', 'year': 1887, 'genre': │
│ 'Mystery', 'main_characters': ['Sherlock Holmes', 'Dr. John Watson', 'Jefferson        │
│ Hope'], 'info': {'bestseller': True}}                                                  │
╰────────────────────────────────────────────────────────────────────────────────────────╯

Describe a book (or 'exit'): Where the detective is a woman.
╭─ Extracted ────────────────────────────────────────────────────────────────────────────╮
│ {'title': 'The Murder at the Vicarage', 'author': 'Agatha Christie', 'year': 1930,     │
│ 'genre': 'Mystery', 'main_characters': ['Miss Jane Marple', 'Colonel Protheroe',       │
│ 'Lawrence Redding'], 'info': {'bestseller': True}}                                     │
╰────────────────────────────────────────────────────────────────────────────────────────╯
```
