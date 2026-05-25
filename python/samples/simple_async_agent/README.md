# LimanAI Simple Async Agent Sample

A sample showing how to run async Liman agent inside a FastAPI server and stream responses to a CLI client over Server-Sent Events (SSE).

Demonstrates:

- Running `Agent` inside a FastAPI request handler
- Streaming agent output to clients via SSE
- Resuming agent state across turns using `ExecutorInput`

## Usage

**Clone the repository**

```bash
git clone https://github.com/gurobokum/liman.git
cd liman/python/samples/simple_async_agent
```

**Install dependencies**

```bash
uv sync
source .venv/bin/activate
```

**Configure environment**

1. Copy `.env.example` to `.env`
2. Set `OPENAI_API_KEY` or `GOOGLE_STUDIO_API_KEY` in `.env`
3. `OPENAI_API_KEY` has priority over `GOOGLE_STUDIO_API_KEY`

**Run the server**

```bash
uv run fastapi run src/server.py
```

to see detailed debug output use

```bash
LIMAN_DEBUG=1 uv run fastapi run src/server.py
```

**Run the client**

In a separate terminal, start the client with a user ID:

```bash
uv run python src/main.py 1
```

Type `exit` or press `Ctrl-C` to quit.

Example session:

```
╭─ Chat ───────────────────────────────────────╮
│ Starting the chat for user_id: 1             │
╰──────────────────────────────────────────────╯
Hi, my name is V
╭─ Agent ──────────────────────────────────────╮
│ Hi V! It's great to meet you.                │
│                                              │
│ How can I help you today?                    │
╰──────────────────────────────────────────────╯
nothing, just talking, what is my name?
╭─ Agent ──────────────────────────────────────╮
│ Your name is V.                              │
╰──────────────────────────────────────────────╯
```
