from urllib.parse import urlparse


def is_url(path: str) -> bool:
    parsed = urlparse(path)
    return bool(parsed.scheme and parsed.netloc)
