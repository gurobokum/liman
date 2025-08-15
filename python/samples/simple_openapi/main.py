import asyncio

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai.chat_models import ChatOpenAI
from liman.agent import Agent
from liman_openapi import create_tool_nodes, load_openapi
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from rich.console import Console
from rich.panel import Panel


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    GOOGLE_STUDIO_API_KEY: SecretStr | None = None
    OPENAI_API_KEY: SecretStr | None = None


settings = Settings()
console = Console()


def confirm_destructive_action(title: str, action: str, user_id: str) -> str:
    console.print(f"{title}? [red]Y/N[/red]", end=": ")
    res = input()
    if res.lower() == "y":
        return f"{action} confirmed. User ID: {user_id}"
    else:
        return "{action} cancelled."


async def main() -> None:
    agent = Agent("./specs", start_node="LLMNode/chat", llm=get_llm())

    # OpenAPI
    openapi = load_openapi("http://localhost:8000/openapi.json")
    create_tool_nodes(openapi, agent.registry, base_url="http://localhost:8000")
    # Uncomment to output the specs into the console
    # agent.registry.print_specs()

    while True:
        input_ = input("Input: ")
        if input_.lower() == "exit":
            break

        print_panel(input_)

        output = await agent.step(input_)

        print_panel(str(output), is_output=True)


def print_panel(text: str, is_output: bool = False) -> None:
    if is_output:
        title = "[bold blue]Agent[/bold blue]"
        border_style = "bold blue"
    else:
        title = "[bold cyan]User[/bold cyan]"
        border_style = "bold cyan"

    console.print(
        Panel(text, title=title, title_align="left", border_style=border_style)
    )


def get_llm() -> ChatOpenAI | ChatGoogleGenerativeAI:
    if settings.OPENAI_API_KEY:
        print("gpt-4o is used as LLM")
        return ChatOpenAI(
            api_key=settings.OPENAI_API_KEY,
            model="gpt-4o",
        )
    elif settings.GOOGLE_STUDIO_API_KEY:
        print("gemini-2.5-flash is used as LLM")
        return ChatGoogleGenerativeAI(
            api_key=settings.GOOGLE_STUDIO_API_KEY, model="gemini-2.5-flash"
        )
    else:
        raise ValueError(
            "Either OPENAI_API_KEY or GOOGLE_STUDIO_API_KEY must be set in the environment."
        )


if __name__ == "__main__":
    asyncio.run(main())
