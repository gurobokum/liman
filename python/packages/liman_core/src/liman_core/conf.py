from pydantic import BaseModel


class Settings(BaseModel):
    DEBUG: bool = False


settings = Settings()


def enable_debug() -> None:
    """
    Enable debug mode for the library.
    """
    global settings
    settings.DEBUG = True
