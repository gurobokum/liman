import asyncio
import os
from pathlib import Path
from uuid import uuid4

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from liman_core.dishka import Scope
from liman_core.node_actor.actor import NodeActor
from liman_core.nodes.llm_node.node import LLMNode
from liman_core.nodes.tool_node.node import ToolNode
from liman_core.registry import Registry
from pydantic import SecretStr

from services import get_location_service

load_dotenv()

SPECS_DIR = Path(__file__).parent / "liman_specs"


async def main() -> None:
    registry = Registry()
    registry.provide(get_location_service, scope=Scope.NODE)

    llm_node = LLMNode.from_yaml_path(
        SPECS_DIR / "assistant_node.yaml", registry=registry
    )
    ToolNode.from_yaml_path(SPECS_DIR / "weather_tool.yaml", registry=registry)

    llm = ChatOpenAI(
        model="gpt-4o",
        api_key=SecretStr(os.environ["OPENAI_API_KEY"]),
    )

    actor = NodeActor.create(llm_node, llm=llm)
    execution_id = uuid4()

    while True:
        try:
            user_input = input("You: ")
        except (KeyboardInterrupt, EOFError):
            break
        if user_input.lower() == "exit":
            break

        result = await actor.execute(user_input, execution_id=execution_id)

        if not result.next_nodes:
            print(f"Assistant: {result.output.content}")
            continue

        tool_messages = []
        for next_node, tool_call in result.next_nodes:
            tool_actor = NodeActor.create(next_node)
            tool_result = await tool_actor.execute(tool_call, execution_id=execution_id)
            tool_messages.append(tool_result.output)

        final_result = await actor.execute(tool_messages, execution_id=execution_id)
        print(f"Assistant: {final_result.output.content}")


if __name__ == "__main__":
    asyncio.run(main())
