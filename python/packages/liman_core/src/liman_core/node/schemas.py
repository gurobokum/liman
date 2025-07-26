from typing import Literal

from liman_core.base import BaseSpec
from liman_core.edge.schemas import EdgeSpec
from liman_core.languages import LocalizedValue


class NodeSpec(BaseSpec):
    kind: Literal["Node"] = "Node"
    name: str
    func: str

    description: LocalizedValue | None = None
    prompts: LocalizedValue | None = None

    nodes: list[str | EdgeSpec] = []
    llm_nodes: list[str | EdgeSpec] = []
    tools: list[str] = []
