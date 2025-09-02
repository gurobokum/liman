from liman_core.nodes.function_node import FunctionNode
from liman_core.nodes.llm_node import LLMNode
from liman_core.nodes.tool_node import ToolNode


def get_node_cls(node_type: str) -> type[LLMNode | ToolNode | FunctionNode]:
    """
    Get node class by type string.

    Maps node type strings to their corresponding node class types
    for dynamic node instantiation.

    Args:
        node_type: String identifier for the node type

    Returns:
        Node class corresponding to the specified type

    Raises:
        ValueError: If node type is not supported
    """
    match node_type:
        case "LLMNode":
            return LLMNode
        case "ToolNode":
            return ToolNode
        case "FunctionNode":
            return FunctionNode
    raise ValueError(f"Unsupported node type: {node_type}")
