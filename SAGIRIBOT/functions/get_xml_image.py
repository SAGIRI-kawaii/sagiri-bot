import aiohttp
import hashlib
from PIL import Image as IMG
from io import BytesIO
import os
from urllib.parse import quote

from graia.application.message.chain import MessageChain
from graia.application.message.elements.internal import Plain
from graia.application.message.elements.internal import Image
from graia.application.message.elements.internal import Xml

from SAGIRIBOT.basics.get_config import get_config


async def get_xml_setu(keyword: str) -> list:
    url = f"https://api.sagiri-web.com/setu/?keyword={quote(keyword)}"
    # print(url)
    async with aiohttp.ClientSession() as session:
        async with session.get(url=url) as resp:
            res = await resp.json()

    data = res["data"][0]
    img_url = data["url"]

    save_base_path = await get_config("setuPath")
    path = save_base_path + f"{data['pid']}_p{data['p']}.png"

    if not os.path.exists(path):
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

        setu_md5 = hashlib.md5(img_content).hexdigest()
        image = IMG.open(BytesIO(img_content))
        image.save(path)
    else:
        with open(path, "rb") as f:
            setu_md5 = hashlib.md5(f.read()).hexdigest()

    image = IMG.open(path)
    x = str(image.size[0])
    y = str(image.size[1])

    xml = f'''
    <?xml version='1.0' encoding='UTF-8' standalone='yes' ?>
        <msg serviceID="5" templateID="1" action="test" brief="[Image]" sourceMsgId="0" url="" flag="2" adverSign="0" multiMsgFlag="0">
            <item layout="0">
                <image uuid="{setu_md5}.png" md5="{setu_md5}" GroupFiledid="0" filesize="38504" local_path="" minWidth="{x}" minHeight="{y}" maxWidth="{x}" maxHeight="{y}" />
            </item>
            <source name="{keyword}setu" icon="" action="web" url="{img_url}" appid="-1" />
        </msg>'''

    print(xml)

    return [
        "quoteSource",
        MessageChain.create([
            Xml(xml=xml)
        ])
    ]