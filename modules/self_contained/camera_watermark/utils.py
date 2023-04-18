import exifread
from io import BytesIO
from pathlib import Path
from base64 import b64encode
from pydantic import BaseModel

from shared.utils.text2img import template2img

brands = {
    "canon", "fujifilm", "hasselblad", "leica", "nikon", "olympus", "panasonic", "pentax", "rioch", "sony", "xiaomi"
}


class ExifData(BaseModel):
    make: str
    model: str
    datetime: str
    exposure_time: str
    f_number: str
    iso: str
    width: str
    length: str
    focal_length: str
    color_space: str
    position: str | None = None
    software: str | None = None


def extract_exif(image: bytes | BytesIO) -> ExifData | None:
    if isinstance(image, bytes):
        image = BytesIO(initial_bytes=image)
    tags = exifread.process_file(image)
    if tags:
        # for i, v in tags.items():
        #     print(f"{i} -> {v}")
        datetime = str(tags.get("Image DateTime", ""))
        datetime = datetime.split(" ")
        if len(datetime) > 1:
            datetime = datetime[0].replace(":", "-") + " " + datetime[1]
        else:
            datetime = str(datetime[0])
        f_number = str(tags.get("EXIF FNumber", ""))
        f_number = f_number.split("/")
        if len(f_number) > 1:
            f_number = round(int(f_number[0]) / int(f_number[1]), 1)
        else:
            f_number = str(f_number[0])
        focal_length = str(tags.get("EXIF FocalLength", ""))
        focal_length = focal_length.split("/")
        if len(focal_length) > 1:
            focal_length = round(int(focal_length[0]) / int(focal_length[1]), 1)
        else:
            focal_length = str(focal_length[0])
        return ExifData(
            make=str(tags["Image Make"]),
            model=str(tags["Image Model"]),
            datetime=datetime,
            exposure_time=str(tags.get("EXIF ExposureTime", -1)),
            f_number=str(f_number),
            iso=str(tags.get("EXIF ISOSpeedRatings", -1)),
            width=str(tags.get("EXIF ExifImageWidth", 0)),
            length=str(tags.get("EXIF ExifImageLength", 0)),
            focal_length=str(focal_length),
            color_space=str(tags.get("EXIF ColorSpace", 0)),
            software=str(tags.get("Image Software"))
        )
    return None


async def gen_watermark(image: bytes | BytesIO) -> bytes | str:
    params = extract_exif(image)
    if not params:
        return "未能读取到exif信息！"
    params = params.dict()
    if isinstance(image, BytesIO):
        image = image.getvalue()
    if params["make"].lower() not in brands:
        return f"不支持的品牌：{params['make']}，当前支持的有：{'、'.join(brands)}"
    brand_image = (Path(__file__).parent / "logo" / f"{params['make'].lower()}.png").read_bytes()
    params["image"] = f"data:image/png;base64,{b64encode(image).decode()}"
    params["brand_image"] = f"data:image/png;base64,{b64encode(brand_image).decode()}"
    return await template2img(Path(__file__).parent / "template.html", params)
