import numpy as np
from PIL import Image as IMG
from io import BytesIO


async def get_max_size(a, b):
    return a if a[0] * a[1] >= b[0] * b[1] else b


async def make_tank(im_1: IMG, im_2: IMG) -> bytes:
    im_1 = im_1.convert("L")
    im_2 = im_2.convert("L")
    max_size = await get_max_size(im_1.size, im_2.size)
    if max_size == im_1.size:
        im_2 = im_2.resize(max_size)
    else:
        im_1 = im_1.resize(max_size)
    arr_1 = np.array(im_1, dtype=np.uint8)
    arr_2 = np.array(im_2, dtype=np.uint8)
    arr_1 = 225 - 70 * ((np.max(arr_1) - arr_1) / (np.max(arr_1) - np.min(arr_1)))
    arr_2 = 30 + 70 * ((arr_2 - np.min(arr_2)) / (np.max(arr_2) - np.min(arr_2)))
    arr_alpha = 255 - (arr_1 - arr_2)
    arr_offset = arr_2 * (255 / arr_alpha)
    arr_new = np.dstack([arr_offset, arr_alpha]).astype(np.uint8)
    if arr_new.shape[0] == 3:
        arr_new = (np.transpose(arr_new, (1, 2, 0)) + 1) / 2.0 * 255.0
    bytesIO = BytesIO()
    IMG.fromarray(arr_new).save(bytesIO, format='PNG')
    return bytesIO.getvalue()
