import imagehash
from PIL import Image as IMG


async def image_hash(img_path: str) -> str:
    """
    Return image hash value

    Args:
        img_path: image path

    Examples:
        hash = await img_hash(path)

    Return:
        str: hash result
    """
    img1 = IMG.open(img_path)
    res = imagehash.dhash(img1)
    print(res)
    return res
