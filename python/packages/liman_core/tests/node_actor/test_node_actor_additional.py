import asyncio
from typing import Any
from unittest.mock import Mock, patch
from uuid import uuid4

import pytest
from langchain_core.language_models.chat_models import BaseChatModel

from liman_core.edge.schemas import EdgeSpec
from liman_core.node_actor import NodeActor, NodeActorStatus
from liman_core.nodes.function_node.node import FunctionNode
from liman_core.nodes.llm_node.node import LLMNode
from liman_core.nodes.tool_node.node import ToolNode
from liman_core.registry import Registry


def test_can_restore_tool_node_ready(tool_node: ToolNode) -> None:
    saved_state = {"status": NodeActorStatus.READY}

    result = NodeActor.can_restore(tool_node, saved_state)

    assert result is True


def test_can_restore_tool_node_executing(tool_node: ToolNode) -> None:
    saved_state = {"status": NodeActorStatus.EXECUTING}

    result = NodeActor.can_restore(tool_node, saved_state)

    assert result is False


def test_can_restore_llm_node_ready(llm_node: LLMNode) -> None:
    saved_state = {"status": NodeActorStatus.READY}

    result = NodeActor.can_restore(llm_node, saved_state)

    assert result is True


def test_can_restore_llm_node_executing(llm_node: LLMNode) -> None:
    saved_state = {"status": NodeActorStatus.EXECUTING}

    result = NodeActor.can_restore(llm_node, saved_state)

    assert result is True


def test_can_restore_llm_node_completed(llm_node: LLMNode) -> None:
    saved_state = {"status": NodeActorStatus.COMPLETED}

    result = NodeActor.can_restore(llm_node, saved_state)

    assert result is True


def test_can_restore_function_node_unsupported(function_node: FunctionNode) -> None:
    saved_state = {"status": NodeActorStatus.READY}

    result = NodeActor.can_restore(function_node, saved_state)

    assert result is False


@pytest.mark.asyncio
async def test_create_or_restore_without_state(function_node: FunctionNode) -> None:
    actor = await NodeActor.create_or_restore(function_node, None)

    assert isinstance(actor, NodeActor)
    assert actor.node == function_node
    assert actor.status == NodeActorStatus.READY


@pytest.mark.asyncio
async def test_create_or_restore_with_state(llm_node: LLMNode) -> None:
    from uuid import uuid4

    saved_state = {
        "status": NodeActorStatus.READY,
        "actor_id": str(uuid4()),
        "node_state": {"kind": "LLMNode", "name": "test"},
    }

    with patch.object(NodeActor, "_restore_state"):
        actor = await NodeActor.create_or_restore(llm_node, saved_state)

        assert isinstance(actor, NodeActor)
        assert actor.node == llm_node


def test_build_evaluation_context_with_dict_output(
    function_actor: NodeActor[FunctionNode],
) -> None:
    output = {"result": "test", "count": 5}

    context, state_context = function_actor._build_evaluation_context(output)

    assert context["$output"] == output
    assert context["$status"] == function_actor.status.value
    assert "$state" in context


def test_build_evaluation_context_with_non_dict_output(
    function_actor: NodeActor[FunctionNode],
) -> None:
    output = "string_result"

    context, state_context = function_actor._build_evaluation_context(output)

    assert context["$output"] == {}
    assert context["$status"] == function_actor.status.value


def test_should_follow_edge_no_condition(
    function_actor: NodeActor[FunctionNode],
) -> None:
    edge = EdgeSpec(target="target_node")
    context: dict[str, Any] = {}
    state_context: dict[str, Any] = {}
    transformer = Mock()

    result = function_actor._should_follow_edge(
        edge, context, state_context, transformer
    )

    assert result is True


def test_should_follow_edge_with_valid_condition(
    function_actor: NodeActor[FunctionNode],
) -> None:
    edge = EdgeSpec(target="target_node", when="true")
    context: dict[str, Any] = {}
    state_context: dict[str, Any] = {}

    with (
        patch("liman_core.node_actor.actor.when_parser") as mock_parser,
        patch("liman_core.node_actor.actor.ConditionalEvaluator") as mock_evaluator,
    ):
        mock_tree = Mock()
        mock_ast = Mock()
        mock_parser.parse.return_value = mock_tree
        transformer = Mock()
        transformer.transform.return_value = mock_ast
        mock_evaluator_instance = Mock()
        mock_evaluator_instance.evaluate.return_value = True
        mock_evaluator.return_value = mock_evaluator_instance

        result = function_actor._should_follow_edge(
            edge, context, state_context, transformer
        )

        assert result is True


def test_should_follow_edge_with_exception(
    function_actor: NodeActor[FunctionNode],
) -> None:
    edge = EdgeSpec(target="target_node", when="invalid_syntax")
    context: dict[str, Any] = {}
    state_context: dict[str, Any] = {}

    with patch("liman_core.node_actor.actor.when_parser") as mock_parser:
        mock_parser.parse.side_effect = Exception("Parse error")
        transformer = Mock()

        result = function_actor._should_follow_edge(
            edge, context, state_context, transformer
        )

        assert result is False


def test_prepare_execution_context(function_actor: NodeActor[FunctionNode]) -> None:
    context = {"key": "value"}
    execution_id = uuid4()

    result = function_actor._prepare_execution_context(context, execution_id)

    assert result["key"] == "value"
    assert result["actor_id"] == function_actor.id
    assert result["execution_id"] == execution_id


def test_get_node_edges_no_edges(function_actor: NodeActor[FunctionNode]) -> None:
    edges = function_actor._get_node_edges()

    assert edges == []


def test_get_node_edges_with_edges(registry: Registry) -> None:
    from liman_core.nodes.function_node.schemas import FunctionNodeSpec
    from liman_core.nodes.node.node import Node

    edge1 = EdgeSpec(target="node1")
    edge2 = EdgeSpec(target="node2")
    spec = FunctionNodeSpec(name="test_node", nodes=[edge1, "string_node", edge2])
    node = FunctionNode(spec, registry)
    actor = NodeActor.create(node)

    edges = actor._get_node_edges()

    assert len(edges) == 2
    assert edges[0] == (Node, edge1)
    assert edges[1] == (Node, edge2)


def test_node_actor_with_custom_id(function_node: FunctionNode) -> None:
    custom_id = uuid4()
    actor = NodeActor(function_node, actor_id=custom_id)

    assert actor.id == custom_id


def test_node_actor_with_llm(llm_node: LLMNode) -> None:
    mock_llm = Mock(spec=BaseChatModel)
    actor = NodeActor(llm_node, llm=mock_llm)

    assert actor.llm == mock_llm


def test_node_actor_error_property(function_actor: NodeActor[FunctionNode]) -> None:
    assert function_actor.error is None


def test_node_actor_execution_lock(function_actor: NodeActor[FunctionNode]) -> None:
    assert isinstance(function_actor._execution_lock, asyncio.Lock)
