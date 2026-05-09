import asyncio
from pathlib import Path

from conf import get_llm
from liman.agent import Agent
from rich.console import Console
from rich.panel import Panel

console = Console()

SPECS_DIR = Path(__file__).parent / "specs"


async def main() -> None:
    agent = Agent(str(SPECS_DIR), start_node="LLMNode/extractor", llm=get_llm())
    # Uncomment to see generated specs
    #print_panel("INITIAL SPEC")
    #agent.registry.print_specs(initial=True)
    #print_panel("COMPILED SPEC")
    #agent.registry.print_specs()

    while True:
        input_ = input("Describe a book (or 'exit'): ")
        if input_.lower() == "exit":
            break

        print_panel(input_)

        output = await agent.step(input_)

        print_panel(str(output), is_output=True)


def print_panel(text: str, is_output: bool = False) -> None:
    if is_output:
        title = "[bold blue]Extracted[/bold blue]"
        border_style = "bold blue"
    else:
        title = "[bold cyan]User[/bold cyan]"
        border_style = "bold cyan"

    console.print(
        Panel(text, title=title, title_align="left", border_style=border_style)
    )


if __name__ == "__main__":
    asyncio.run(main())
