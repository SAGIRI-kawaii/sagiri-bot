import aiohttp
from PIL import Image as IMG
from io import BytesIO

from graia.application.message.chain import MessageChain
from graia.application.message.elements.internal import Plain
from graia.application.message.elements.internal import Image

from functions.data_manage.update_data.set_get_image_ready import set_get_img_ready
from functions.data_manage.get_data.get_total_calls import get_total_calls
from functions.data_manage.update_data.update_total_calls import update_total_calls
from functions.basics.get_config import get_config


async def search_image(group_id: int, sender: int, img: Image) -> list:
    """
    Return search result

    Args:
        group_id: Group id
        sender: Sender
        img: Image to search

    Examples:
        message = await search_image(group_id, sender, image)

    Return:
        [
            str: Auxiliary treatment to be done(Such as add statement),
            MessageChain: Message to be send(MessageChain)
        ]
    """
    await set_get_img_ready(group_id, sender, False, "searchReady")
    search_total_count = await get_total_calls("search") + 1
    await update_total_calls(search_total_count, "search")
    path = "%s%s.png" % (await get_config("searchPath"), search_total_count)
    async with aiohttp.ClientSession() as session:
        async with session.get(url=img.url) as resp:
            img_content = await resp.read()
    image = IMG.open(BytesIO(img_content))
    image.save(path)

    # url for headers
    url = "https://saucenao.com/search.php"

    # picture url
    pic_url = img.url

    # json requesting url
    url2 = f"https://saucenao.com/search.php?db=999&output_type=2&testmode=1&numres=1&url={pic_url}"

    # data for posting.
    payload = {
        "url": pic_url,
        "numres": 1,
        "testmode": 1,
        "db": 999,
        "output_type": 2,
    }

    # header to fool the website.
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Referer": url,
        "Origin": "https://saucenao.com",
        "Host": "saucenao.com"
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url=url, headers=headers, data=payload) as resp:
            json_data = await resp.json()

    # print thumbnail URL.
    # print(json_data)
    # print(json_data["results"][0]["header"]["thumbnail"])

    path = "M:\\pixiv\\Thumbnail\\%s.png" % search_total_count
    async with aiohttp.ClientSession() as session:
        async with session.post(url=url, headers=headers, data=payload) as resp:
            json_data = await resp.json()

    async with aiohttp.ClientSession() as session:
        async with session.get(url=json_data["results"][0]["header"]["thumbnail"]) as resp:
            img_content = await resp.read()

    image = IMG.open(BytesIO(img_content))
    image.save(path)
    similarity = json_data["results"][0]["header"]["similarity"]
    try:
        pixiv_url = json_data["results"][0]["data"]["ext_urls"][0]
    except KeyError:
        pixiv_url = "None"
    if "pixiv_id" not in json_data["results"][0]["data"]:
        if "source" not in json_data["results"][0]["data"]:
            # record("search", path, sender, group_id, False, "img")
            return [
                "quoteSource",
                MessageChain.create([
                    Plain(text="8好意思~没有找到相似的图诶~")
                ])
            ]
        else:
            try:
                creator = json_data["results"][0]["data"]["creator"][0]
            except Exception:
                creator = "Unknown!"
            # record("search",dist,sender,groupId,True,"img")
            return [
                "quoteSource",
                MessageChain.create([
                    Plain(text="这个结果相似度很低诶。。。。要不你康康？\n"),
                    Image.fromLocalFile(path),
                    Plain(text="\n相似度:%s%%\n"%(similarity)),
                    Plain(text="原图地址:%s\n"%pixiv_url),
                    Plain(text="作者:%s\n"%creator),
                    Plain(text="如果不是你想找的图的话可能因为这张图是最近才画出来的哦，网站还未收录呢~过段日子再来吧~")
                ])
            ]
    else:
        pixiv_id = json_data["results"][0]["data"]["pixiv_id"]
        user_name = json_data["results"][0]["data"]["member_name"]
        user_id = json_data["results"][0]["data"]["member_id"]
        # record("search",dist,sender,groupId,True,"img")
        return [
            "quoteSource",
            MessageChain.create([
                Image.fromLocalFile(path),
                Plain(text="\n相似度:%s%%\n" % (similarity)),
                Plain(text="原图地址:%s\n" % pixiv_url),
                Plain(text="作品id:%s\n" % pixiv_id),
                Plain(text="作者名字:%s\n" % user_name),
                Plain(text="作者id:%s\n" % user_id)
            ])
        ]