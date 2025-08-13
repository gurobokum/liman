from liman_core.nodes.function_node import FunctionNode
from liman_core.nodes.llm_node import LLMNode
from liman_core.nodes.tool_node import ToolNode


def get_node_cls(node_type: str) -> type[LLMNode | ToolNode | FunctionNode]:
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
        case "FunctionNode":
            return FunctionNode
    raise ValueError(f"Unsupported node type: {node_type}")
