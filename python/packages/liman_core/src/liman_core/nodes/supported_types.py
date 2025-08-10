from liman_core.llm_node import LLMNode
from liman_core.node import Node
from liman_core.tool_node import ToolNode


def get_node_cls(node_type: str) -> type[LLMNode | ToolNode | Node]:
    """
    Get the Node class based on the node type.

    Args:
        node_type (str): The type of the node.

    Returns:
        type[Node]: The corresponding Node class.
    """
    match node_type:
        case "LLMNode":
            return LLMNode
        case "ToolNode":
            return ToolNode
        case "Node":
            return Node
        case _:
            return Node
