from collections.abc import Generator
from unittest.mock import AsyncMock, patch

import pytest
from langchain_core.messages import AIMessage
from liman_core.nodes.llm_node.node import LLMNode
from liman_core.registry import Registry

from liman.state import InMemoryStateStorage


@pytest.fixture
def registry() -> Registry:
    return Registry()


@pytest.fixture
def storage() -> InMemoryStateStorage:
    return InMemoryStateStorage()


@pytest.fixture
def llm_node(registry: Registry) -> Generator[LLMNode, None, None]:
    node_dict = {
        "kind": "LLMNode",
        "name": "test_llm_node",
        "prompts": {
            "system": {"en": "You are a helpful assistant."},
        },
    }
    with patch.object(LLMNode, "invoke", new_callable=AsyncMock) as mock_invoke:
        mock_invoke.return_value = AIMessage("llm_result")
        node = LLMNode.from_dict(node_dict, registry)
        node.compile()
        yield node
