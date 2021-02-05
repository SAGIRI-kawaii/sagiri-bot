import aiohttp
import hashlib
from PIL import Image as IMG
from io import BytesIO
import os
from urllib.parse import quote

from graia.application import GraiaMiraiApplication
from graia.application.entities import UploadMethods
from graia.application.message.chain import MessageChain
from graia.application.message.elements.internal import Plain
from graia.application.message.elements.internal import Image
from graia.application.message.elements.internal import Xml

from SAGIRIBOT.basics.get_config import get_config


async def get_xml_setu(keyword: str, app: GraiaMiraiApplication) -> list:
    url = f"https://api.sagiri-web.com/setu/?keyword={quote(keyword)}"
    # print(url)
    async with aiohttp.ClientSession() as session:
        async with session.get(url=url) as resp:
            res = await resp.json()

    data = res["data"][0]
    img_url = data["url"]
    title = data["title"]

    save_base_path = await get_config("setuPath")
    path = save_base_path + f"{data['pid']}_p{data['p']}.png"

    if not os.path.exists(path):
        print("downloading")
        async with aiohttp.ClientSession() as session:
            async with session.get(url=img_url) as resp:
                img_content = await resp.read()
                code = resp.status

        if code == 404:
            return [
                "quoteSource",
                MessageChain.create([
                    Plain(text="404 Not Found!")
                ])
            ]

        # upload_resp = await app.uploadImage(img_content, UploadMethods.Group, return_external=True)
        # href = upload_resp.url
        # image_id = upload_resp.imageId
        # upload_path = upload_resp.path
        # setu_md5 = hashlib.md5(img_content).hexdigest()
        image = IMG.open(BytesIO(img_content))
        image.save(path)
    with open(path, "rb") as f:
        img_content = f.read()
        setu_md5 = hashlib.md5(img_content).hexdigest()
        upload_resp = await app.uploadImage(img_content, UploadMethods.Group, return_external=True)
        href = upload_resp.url
        image_id = upload_resp.imageId
        upload_path = upload_resp.path
        print(href)
    image = IMG.open(path)
    x = str(image.size[0])
    y = str(image.size[1])

    xml = f'''
    <?xml version='1.0' encoding='UTF-8' standalone='yes' ?>
        <msg serviceID="5" templateID="1" action="test" brief="[Image]" sourceMsgId="0" url="" flag="2" adverSign="0" multiMsgFlag="0">
            <item layout="0">
                <image uuid="{image_id}" md5="{setu_md5.upper()}" GroupFiledid="0" filesize="81322" local_path="" minWidth="{x}" minHeight="{y}" maxWidth="{x}" maxHeight="{y}" />
            </item>
            <source name="{title}" icon="" action="" url="" appid="-1" />
        </msg>'''

    xml2 = f'''
    <?xml version='1.0' encoding='UTF-8' standalone='yes' ?>
    <msg serviceID="5" templateID="12345" action="" brief="不够涩！" sourceMsgId="0" url="" flag="0" adverSign="0" multiMsgFlag="0">
        <item layout="0" advertiser_id="0" aid="0">
            <image uuid="{image_id}" md5="{setu_md5.upper()}" GroupFiledid="0" filesize="81322" local_path="{upload_path}" minWidth="{x}" minHeight="{y}" maxWidth="{x}" maxHeight="{y}" />
        </item>
        <source name="{title}" icon="" action="" appid="-1" />
    </msg>
'''

    print(xml2)

    return [
        "quoteSource",
        MessageChain.create([
            Xml(xml=xml2)
        ])
    ]