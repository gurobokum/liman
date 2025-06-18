from liman_core import __version__
from proto.liman_pb2 import Prompt


def main() -> None:
    print("Hello from Liman! with liman_core version:", __version__)
    prompt = Prompt(api_version="1.0", kind="example")
    print(
        f"Prompt created with API version: {prompt.api_version} and kind: {prompt.kind}"
    )
