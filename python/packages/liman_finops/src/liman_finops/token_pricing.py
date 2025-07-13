import logging

logger = logging.getLogger(__name__)


def calculate_token_price(
    input_tokens: float, cached_tokens: float, output_tokens: float
) -> tuple[float, float, float]:
    """
    Calculate the token price based on the number of tokens.

    Returns a tuple of (input_token_price, output_token_price, cached_token_price).
    """
    return (
        input_tokens / 1_000_000,
        cached_tokens / 1_000_000,
        output_tokens / 1_000_000,
    )


DEFAULT = calculate_token_price(1, 0, 4.5)
# https://platform.openai.com/docs/pricing
GPT_4_1 = calculate_token_price(2, 0.5, 8)
GPT_4_1_MINI = calculate_token_price(0.4, 0.1, 1.6)
GPT_4_1_NANO = calculate_token_price(0.1, 0.025, 0.4)
GPT_4_5_PREVIEW = calculate_token_price(75, 37.5, 150)
GPT_4O = calculate_token_price(2.5, 1.25, 10)
GTP_4O_AUDIO_PREVIEW = calculate_token_price(2.5, 0, 10)
GPT_4O_REALTIME_PREVIEW = calculate_token_price(5, 2.5, 20)
GPT_4O_MINI = calculate_token_price(0.15, 0.075, 0.6)
GPT_4O_MINI_AUDIO_PREVIEW = calculate_token_price(0.15, 0, 0.6)
GPT_4O_MINI_REALTIME_PREVIEW = calculate_token_price(0.6, 0.3, 2.4)
GPT_3_5_TURBO = calculate_token_price(0.5, 0, 1.5)


def get_token_price(model_name: str) -> tuple[float, float, float]:
    """
    Get the token price for the specified model.

    Returns a tuple of (input_token_price, output_token_price, cached_token_price).
    """

    match model_name:
        case "gpt-4.1":
            return GPT_4_1
        case "gpt-4.1-mini":
            return GPT_4_1_MINI
        case "gpt-4.1-nano":
            return GPT_4_1_NANO
        case "gpt-4.5-preview":
            return GPT_4_5_PREVIEW
        case "gpt-4o":
            return GPT_4O
        case "gpt-4o-audio-preview":
            return GTP_4O_AUDIO_PREVIEW
        case "gpt-4o-realtime-preview":
            return GPT_4O_REALTIME_PREVIEW
        case "gpt-4o-mini":
            return GPT_4O_MINI
        case "gpt-4o-mini-audio-preview":
            return GPT_4O_MINI_AUDIO_PREVIEW
        case "gpt-4o-mini-realtime-preview":
            return GPT_4O_MINI_REALTIME_PREVIEW
        case "gpt-3.5-turbo":
            return GPT_3_5_TURBO
        case _:
            logger.warning(
                "Unknown model name '%s'. Using default token prices.", model_name
            )
            return DEFAULT
