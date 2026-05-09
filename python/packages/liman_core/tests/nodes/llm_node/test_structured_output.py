from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_core.messages import AIMessage, HumanMessage

from liman_core.errors import LimanError
from liman_core.node_actor.actor import NodeActor
from liman_core.nodes.base.schemas import StructuredOutput
from liman_core.nodes.llm_node.node import LLMNode
from liman_core.nodes.llm_node.schemas import LLMNodeState
from liman_core.nodes.llm_node.structured_output import StructuredOutputSpec
from liman_core.registry import Registry

SIMPLE_SPEC = {
    "kind": "LLMNode",
    "name": "extractor",
    "prompts": {"system": {"en": "Extract info."}},
    "structured_output": {"name": "str", "age": "int"},
}

EXPECTED_SCHEMA = {
    "title": "extractor",
    "type": "object",
    "properties": {"name": {"type": "string"}, "age": {"type": "integer"}},
    "required": ["name", "age"],
}


@pytest.fixture
def registry() -> Registry:
    return Registry()


def make_node(spec: dict[str, Any], registry: Registry) -> LLMNode:
    return LLMNode.from_dict(spec, registry)


def test_spec_parses_structured_output(registry: Registry) -> None:
    node = make_node(SIMPLE_SPEC, registry)
    assert isinstance(node.spec.structured_output, StructuredOutputSpec)
    assert len(node.spec.structured_output.fields) == 2


def test_compile_builds_output_spec(registry: Registry) -> None:
    node = make_node(SIMPLE_SPEC, registry)
    node.compile()
    assert node.spec.structured_output is not None


def test_compile_raises_when_tools_and_structured_output(registry: Registry) -> None:
    spec = {**SIMPLE_SPEC, "tools": ["SomeTool"]}
    node = make_node(spec, registry)
    with pytest.raises(LimanError, match="cannot be used together"):
        node.compile()


def test_compile_raises_on_empty_structured_output(registry: Registry) -> None:
    spec = {**SIMPLE_SPEC, "structured_output": {}}
    node = make_node(spec, registry)
    with pytest.raises(LimanError, match="must not be empty"):
        node.compile()


def test_no_schema_compile_leaves_output_spec_none(registry: Registry) -> None:
    spec = {
        "kind": "LLMNode",
        "name": "plain",
        "prompts": {"system": {"en": "You are a helpful assistant."}},
    }
    node = make_node(spec, registry)
    node.compile()
    assert node.spec.structured_output is None


@pytest.mark.asyncio
async def test_invoke_uses_with_structured_output(registry: Registry) -> None:
    node = make_node(SIMPLE_SPEC, registry)
    node.compile()

    result_data = {"name": "Alice", "age": 30}
    structured_chain = AsyncMock(return_value=result_data)
    llm = MagicMock()
    llm.with_structured_output.return_value.ainvoke = structured_chain

    result = await node.invoke(llm, [HumanMessage(content="hello")])

    llm.with_structured_output.assert_called_once_with(EXPECTED_SCHEMA)
    assert isinstance(result, StructuredOutput)
    assert result.is_structured_output is True
    assert result.content == [result_data]


@pytest.mark.asyncio
async def test_invoke_normal_path_unchanged(registry: Registry) -> None:
    spec = {
        "kind": "LLMNode",
        "name": "plain",
        "prompts": {"system": {"en": "You are helpful."}},
    }
    node = make_node(spec, registry)
    node.compile()

    ai_message = AIMessage(content="hello")
    llm = AsyncMock()
    llm.ainvoke.return_value = ai_message

    result = await node.invoke(llm, [HumanMessage(content="hi")])

    assert result is ai_message
    llm.ainvoke.assert_called_once()


@pytest.mark.asyncio
async def test_execute_llm_node_returns_structured_output(registry: Registry) -> None:
    result_data = {"name": "Alice", "age": 30}
    structured_output = StructuredOutput(content=[result_data])

    with patch.object(LLMNode, "invoke", new_callable=AsyncMock) as mock_invoke:
        mock_invoke.return_value = structured_output
        node = make_node(SIMPLE_SPEC, registry)
        node.compile()
        actor: NodeActor[LLMNode] = NodeActor(node=node, llm=AsyncMock())

        output = await actor._execute_llm_node(input_="Extract info about Alice")

    assert output is structured_output

    node_state = actor.node_state
    assert isinstance(node_state, LLMNodeState)
    assert node_state.messages[-1] is structured_output


def test_compile_injects_output_format_into_system_prompt(registry: Registry) -> None:
    spec = {
        "kind": "LLMNode",
        "name": "extractor",
        "prompts": {"system": {"en": "Extract info."}},
        "structured_output": {
            "name": {"type": "str", "description": "Full name"},
            "age": "int",
            "notes?": "str",
        },
    }
    node = make_node(spec, registry)
    node.compile()

    content = node.prompts.to_system_message("en").content
    assert 'name: "string, Full name"' in content
    assert 'age: "integer"' in content
    assert 'notes: "string, optional"' in content


def test_compile_injects_output_format_all_languages(registry: Registry) -> None:
    spec = {
        "kind": "LLMNode",
        "name": "extractor",
        "prompts": {
            "en": {"system": "Extract info."},
            "ru": {"system": "Извлеки информацию."},
        },
        "structured_output": {"title": "str"},
    }
    node = make_node(spec, registry)
    node.compile()

    for lang in ("en", "ru"):
        content = node.prompts.to_system_message(lang).content
        assert 'title: "string"' in content


def test_compile_no_output_format_without_structured_output(registry: Registry) -> None:
    spec = {
        "kind": "LLMNode",
        "name": "plain",
        "prompts": {"system": {"en": "You are helpful."}},
    }
    node = make_node(spec, registry)
    node.compile()

    content = node.prompts.to_system_message("en").content
    assert "Output format:" not in content


@pytest.mark.asyncio
async def test_execute_llm_node_normal_path_unchanged(registry: Registry) -> None:
    ai_message = AIMessage(content="response")

    with patch.object(LLMNode, "invoke", new_callable=AsyncMock) as mock_invoke:
        mock_invoke.return_value = ai_message
        spec = {
            "kind": "LLMNode",
            "name": "plain",
            "prompts": {"system": {"en": "You are helpful."}},
        }
        node = make_node(spec, registry)
        node.compile()
        actor: NodeActor[LLMNode] = NodeActor(node=node, llm=AsyncMock())

        output = await actor._execute_llm_node(input_="hi")

    assert output is ai_message

    node_state = actor.node_state
    assert isinstance(node_state, LLMNodeState)
    assert node_state.messages[-1] is ai_message
