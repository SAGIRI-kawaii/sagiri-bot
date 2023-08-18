import hashlib
from typing import Literal


def get_image_type(data: bytes) -> Literal["JPEG", "PNG", "GIF", "BMP", "Unknown"]:
    if data.startswith(b"\xFF\xD8"):
        return "JPEG"
    elif data.startswith(b"\x89\x50\x4E\x47"):
        return "PNG"
    elif data.startswith(b"\x47\x49\x46\x38"):
        return "GIF"
    elif data.startswith(b"\x42\x4D"):
        return "BMP"
    else:
        return "Unknown"


def get_md5(raw: bytes) -> str:
    md5_hash = hashlib.md5()
    md5_hash.update(raw)
    return md5_hash.hexdigest().upper()
