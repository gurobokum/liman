import logging

from liman_core.errors import LimanError
from liman_core.llm import resolve_model

logger = logging.getLogger(__name__)


def calculate_token_price(
    input_tokens: float, cached_tokens: float, output_tokens: float
) -> tuple[float, float, float]:
    """
    Calculate the token price based on the number of tokens.

    Returns a tuple of (input_token_price, cached_token_price, output_token_price).
    """
    return (
        input_tokens / 1_000_000,
        cached_tokens / 1_000_000,
        output_tokens / 1_000_000,
    )


DEFAULT = calculate_token_price(1, 0, 4.5)


def get_token_price(model_name: str) -> tuple[float, float, float]:
    """
    Get the token price for the model from the liman_core model registry.

    Returns a tuple of (input_token_price, cached_token_price, output_token_price).
    Falls back to DEFAULT for unknown models or models without pricing.
    """
    try:
        info = resolve_model(model_name)
    except LimanError:
        logger.warning(
            "Unknown model name '%s'. Using default token prices.", model_name
        )
        return DEFAULT

    if info.pricing is None:
        return DEFAULT
    pricing = info.pricing
    return calculate_token_price(pricing.input, pricing.cached, pricing.output)
