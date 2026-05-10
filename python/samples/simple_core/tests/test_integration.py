from unittest.mock import AsyncMock
from uuid import uuid4

from langchain_core.messages import AIMessage
from liman_core.node_actor.actor import NodeActor
from liman_core.nodes.llm_node.node import LLMNode
from liman_core.nodes.tool_node.node import ToolNode


async def test_direct_answer(actor: NodeActor[LLMNode], mock_llm: AsyncMock) -> None:
    mock_llm.ainvoke.return_value = AIMessage(
        content="I can help with weather information."
    )

    result = await actor.execute("Hello!", uuid4())

    assert result.next_nodes == []
    assert result.output.content == "I can help with weather information."


async def test_weather_with_explicit_location(
    actor: NodeActor[LLMNode], mock_llm: AsyncMock, tool_node: ToolNode
) -> None:
    execution_id = uuid4()
    mock_llm.ainvoke.side_effect = [
        AIMessage(
            content="",
            tool_calls=[
                {
                    "name": "weather_tool",
                    "args": {"location": "london"},
                    "id": "call_1",
                    "type": "tool_call",
                }
            ],
        ),
        AIMessage(content="London is 15.0°C and cloudy."),
    ]

    first_result = await actor.execute("What's the weather in London?", execution_id)

    assert len(first_result.next_nodes) == 1
    next_node, tool_call = first_result.next_nodes[0]

    tool_actor = NodeActor.create(next_node)
    tool_result = await tool_actor.execute(tool_call, execution_id)

    assert "15.0" in tool_result.output.content
    assert "cloudy" in tool_result.output.content

    final_result = await actor.execute([tool_result.output], execution_id)
    assert final_result.output.content == "London is 15.0°C and cloudy."


async def test_weather_without_location(
    actor: NodeActor[LLMNode], mock_llm: AsyncMock, tool_node: ToolNode
) -> None:
    execution_id = uuid4()
    mock_llm.ainvoke.side_effect = [
        AIMessage(
            content="",
            tool_calls=[
                {
                    "name": "weather_tool",
                    "args": {},
                    "id": "call_2",
                    "type": "tool_call",
                }
            ],
        ),
        AIMessage(content="Here's your local weather."),
    ]

    first_result = await actor.execute("What's the weather?", execution_id)

    assert len(first_result.next_nodes) == 1
    _, tool_call = first_result.next_nodes[0]

    tool_actor = NodeActor.create(tool_node)
    tool_result = await tool_actor.execute(tool_call, execution_id)

    assert "London" in tool_result.output.content
    assert "15.0" in tool_result.output.content

    final_result = await actor.execute([tool_result.output], execution_id)
    assert final_result.output.content == "Here's your local weather."
