import asyncio
from asyncio import Queue
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal, TypedDict
from uuid import UUID, uuid4

from fastapi import FastAPI, Header, HTTPException
from fastapi.sse import EventSourceResponse
from liman.agent import Agent
from liman.executor.schemas import ExecutorInput, ExecutorOutput
from pydantic import Field
from pydantic.main import BaseModel

from conf import get_llm

shutdown_event = asyncio.Event()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    shutdown_event.clear()
    yield
    shutdown_event.set()


app = FastAPI(
    title="Simple Async Liman Agent",
    description="Your async agent for Liman, built with FastAPI",
    version="1.0.0",
    lifespan=lifespan,
)


class Message(BaseModel):
    id: UUID = Field(default_factory=lambda: uuid4())
    from_: Literal["user", "agent"]
    chat_id: UUID
    content: str


class MessageRequest(BaseModel):
    content: str


class Chat(BaseModel):
    id: UUID = Field(default_factory=lambda: uuid4())
    messages: list[Message] = Field(default_factory=list)


class DB(TypedDict):
    chats: dict[UUID, list[Message]]
    agents: dict[int, ExecutorOutput]


db: DB = {"chats": {}, "agents": {}}
queues: dict[UUID, Queue[Message]] = {}


@app.get("/chat/{chat_id}", response_model=Chat)
def get_chat(chat_id: UUID) -> Chat:
    messages = db.get("chats", {}).get(chat_id, [])
    return Chat(id=chat_id, messages=messages)


@app.put("/chat/message", response_model=Chat)
async def create_chat(body: MessageRequest, x_user_id: int = Header()) -> Chat:
    chat = Chat()
    message = Message(content=body.content, chat_id=chat.id, from_="user")
    db["chats"][chat.id] = [message]

    queue = queues.get(chat.id, Queue())
    queues[chat.id] = queue
    await queue.put(message)

    return chat


@app.put("/chat/{chat_id}/message", response_model=Message)
async def send_message(chat_id: UUID, body: MessageRequest, x_user_id: int = Header()) -> Message:
    messages = db.get("chats", {}).get(chat_id)
    if messages is None:
        raise HTTPException(status_code=404, detail=f"Chat with ID {chat_id} not found")

    message = Message(content=body.content, chat_id=chat_id, from_="user")
    messages.append(message)

    queue = queues[chat_id]
    await queue.put(message)
    return message


@app.get("/chat/{chat_id}/stream")
async def stream_messages(chat_id: UUID, x_user_id: int = Header()) -> EventSourceResponse:
    if chat_id not in queues:
        raise HTTPException(status_code=404, detail=f"Chat with ID {chat_id} not found")

    agent = Agent(str(Path(__file__).parent / "specs"), start_node="LLMNode/chat", llm=get_llm())
    queue = queues[chat_id]

    async def generate() -> AsyncIterator[str]:
        while not shutdown_event.is_set():
            try:
                message = await asyncio.wait_for(queue.get(), timeout=0.5)
            except asyncio.TimeoutError:
                continue

            input_: ExecutorInput | str = message.content
            if last_output := db["agents"].get(x_user_id):
                input_ = ExecutorInput.model_validate(
                    {**last_output.model_dump(), "node_input": message.content}
                )
            output = await agent.step(input_)
            queue.task_done()
            db["agents"][x_user_id] = output
            yield str(output)

    return EventSourceResponse(generate())
