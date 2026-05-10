from pathlib import Path
from unittest.mock import AsyncMock

import pytest
from liman_core.dishka import Scope
from liman_core.node_actor.actor import NodeActor
from liman_core.nodes.llm_node.node import LLMNode
from liman_core.nodes.tool_node.node import ToolNode
from liman_core.registry import Registry
from services import LocationService

SPECS_DIR = Path(__file__).parent.parent / "src" / "liman_specs"


def fixed_location_service() -> LocationService:
    return LocationService("London")


@pytest.fixture
def registry() -> Registry:
    r = Registry()
    r.provide(fixed_location_service, scope=Scope.NODE)
    return r


@pytest.fixture
def tool_node(registry: Registry) -> ToolNode:
    return ToolNode.from_yaml_path(SPECS_DIR / "weather_tool.yaml", registry=registry)


@pytest.fixture
def llm_node(registry: Registry, tool_node: ToolNode) -> LLMNode:
    return LLMNode.from_yaml_path(SPECS_DIR / "assistant_node.yaml", registry=registry)


@pytest.fixture
def mock_llm() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def actor(llm_node: LLMNode, mock_llm: AsyncMock) -> NodeActor[LLMNode]:
    return NodeActor.create(llm_node, llm=mock_llm)
