import hashlib


def string_to_unique_number(input_string: str) -> int:
    sha256_hash = hashlib.sha256(input_string.encode()).hexdigest()
    unique_number = int(sha256_hash, 16)
    return unique_number