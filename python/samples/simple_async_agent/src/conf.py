from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai.chat_models import ChatOpenAI
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    GOOGLE_STUDIO_API_KEY: SecretStr | None = None
    OPENAI_API_KEY: SecretStr | None = None


settings = Settings()


def get_llm() -> ChatOpenAI | ChatGoogleGenerativeAI:
    if settings.OPENAI_API_KEY:
        print("gpt-5.4-mini is used as LLM")
        return ChatOpenAI(
            api_key=settings.OPENAI_API_KEY,
            model="gpt-5.4-mini",
        )
    elif settings.GOOGLE_STUDIO_API_KEY:
        print("gemini-2.5-flash is used as LLM")
        return ChatGoogleGenerativeAI(
            api_key=settings.GOOGLE_STUDIO_API_KEY, model="gemini-2.5-flash"
        )
    else:
        raise ValueError(
            "Either OPENAI_API_KEY or GOOGLE_STUDIO_API_KEY must be set in the environment."
        )
