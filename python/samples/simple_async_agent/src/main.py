import asyncio
import signal
import sys
from uuid import UUID

from aioconsole import ainput, aprint
from httpx import AsyncClient
from rich.console import Console
from rich.panel import Panel

console = Console()

BASE_URL = "http://localhost:8000"


async def main(user_id: int) -> None:
    chat_id = None
    sse_task: asyncio.Task[None] | None = None

    def stop() -> None:
        if main_task := asyncio.current_task():
            main_task.cancel()

    loop = asyncio.get_running_loop()
    loop.add_signal_handler(signal.SIGTERM, stop)

    await print_panel(f"Starting the chat for user_id: {user_id}")

    async with AsyncClient() as client:
        try:
            while True:
                input_ = await ainput()
                if input_.lower() == "exit":
                    break

                if chat_id is None:
                    response = await client.put(
                        f"{BASE_URL}/chat/message",
                        headers={"X-User-ID": str(user_id)},
                        json={"content": input_},
                    )
                    chat_id = response.json()["id"]
                    sse_task = asyncio.create_task(sse(user_id, chat_id))
                else:
                    await client.put(
                        f"{BASE_URL}/chat/{chat_id}/message",
                        headers={"X-User-ID": str(user_id)},
                        json={"content": input_},
                    )
        except asyncio.CancelledError:
            pass
        finally:
            if sse_task and not sse_task.done():
                sse_task.cancel()
                await asyncio.gather(sse_task, return_exceptions=True)


async def sse(user_id: int, chat_id: UUID) -> None:
    """
    Listens for async Server-Sent Events (SSE) from the server for the given chat_id
    and prints each event as it arrives.
    """
    try:
        async with (
            AsyncClient() as client,
            client.stream(
                "GET",
                f"{BASE_URL}/chat/{chat_id}/stream",
                headers={"X-User-ID": str(user_id)},
                timeout=None,
            ) as response,
        ):
            try:
                async for text in response.aiter_text():
                    await print_panel(text, is_output=True)
            except asyncio.CancelledError:
                pass
    except Exception as e:
        print(f"Error in SSE stream: {e}")


async def print_panel(text: str, is_output: bool = False) -> None:
    if is_output:
        title = "[bold blue]Agent[/bold blue]"
        border_style = "bold blue"
    else:
        title = "[bold cyan]Chat[/bold cyan]"
        border_style = "bold cyan"

    with console.capture() as capture:
        console.print(Panel(text, title=title, title_align="left", border_style=border_style))

    await aprint(capture.get(), end="")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: main.py <user_id>", file=sys.stderr)
        sys.exit(1)
    asyncio.run(main(int(sys.argv[1])))
