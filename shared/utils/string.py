import hashlib
from base64 import b64encode


def string_to_unique_number(input_string: str) -> int:
    sha256_hash = hashlib.sha256(input_string.encode()).hexdigest()
    unique_number = int(sha256_hash, 16)
    return unique_number


def string2b64(content: str) -> str:
    return b64encode(content.encode("utf-8")).decode("utf-8")