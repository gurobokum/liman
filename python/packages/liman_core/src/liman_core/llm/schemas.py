from pydantic import BaseModel, Field


class Pricing(BaseModel):
    """
    USD per 1M tokens.
    """

    input: float
    cached: float = 0.0
    output: float


class ModelDef(BaseModel):
    pricing: Pricing | None = None


class ProviderDef(BaseModel):
    package: str
    module: str
    cls: str = Field(alias="class")
    env_key: str | None = None
    models: dict[str, ModelDef] = {}


class ModelsRegistry(BaseModel):
    providers: dict[str, ProviderDef]
