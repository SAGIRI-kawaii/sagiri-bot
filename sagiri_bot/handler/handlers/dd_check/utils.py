import json
import jinja2
import asyncio
from pathlib import Path
from loguru import logger
from typing import List, Union

from graia.ariadne import get_running
from graia.ariadne.adapter import Adapter

from utils.html2pic import html_to_pic
from sagiri_bot.core.app_core import AppCore


vtb_list_path = Path(__file__).parent / "vtb_list.json"
config = AppCore.get_core_instance().get_config()
dir_path = Path(__file__).parent
template_path = dir_path / "template"
env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(str(template_path)), enable_async=True
)


async def update_vtb_list():
    vtb_list = []
    urls = [
        "https://api.vtbs.moe/v1/short",
        "https://api.tokyo.vtbs.moe/v1/short",
        "https://vtbs.musedash.moe/v1/short",
    ]
    for url in urls:
        try:
            async with get_running(Adapter).session.get(url, timeout=10) as resp:
                result = await resp.json()
            if not result:
                continue
            for info in result:
                if info.get("mid", None) and info.get("uname", None):
                    vtb_list.append(info)
            break
        except asyncio.TimeoutError:
            logger.warning(f"Get {url} timeout")
    dump_vtb_list(vtb_list)


def load_vtb_list() -> List[dict]:
    if vtb_list_path.exists():
        with vtb_list_path.open("r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.decoder.JSONDecodeError:
                logger.warning("vtb列表解析错误，将重新获取")
                vtb_list_path.unlink()
    return []


def dump_vtb_list(vtb_list: List[dict]):
    json.dump(
        vtb_list,
        vtb_list_path.open("w", encoding="utf-8"),
        indent=4,
        separators=(",", ": "),
        ensure_ascii=False,
    )


async def get_vtb_list() -> List[dict]:
    vtb_list = load_vtb_list()
    if not vtb_list:
        await update_vtb_list()
    return load_vtb_list()


async def get_uid_by_name(name: str) -> int:
    try:
        url = "http://api.bilibili.com/x/web-interface/search/type"
        params = {"search_type": "bili_user", "keyword": name}
        async with get_running(Adapter).session.get(url, params=params, timeout=10) as resp:
            result = await resp.json()
        for user in result["data"]["result"]:
            if user["uname"] == name:
                return user["mid"]
        return 0
    except (KeyError, IndexError, asyncio.TimeoutError) as e:
        logger.warning(f"Error in get_uid_by_name({name}): {e}")
        return 0


async def get_user_info(uid: int) -> dict:
    try:
        url = "https://account.bilibili.com/api/member/getCardByMid"
        params = {"mid": uid}
        async with get_running(Adapter).session.get(url, params=params, timeout=10) as resp:
            result = await resp.text()
        result = json.loads(result)
        return result["card"]
    except (KeyError, IndexError, asyncio.TimeoutError) as e:
        logger.warning(f"Error in get_user_info({uid}): {e}")
        return {}


async def get_medals(uid: int) -> List[dict]:
    try:
        url = "https://api.live.bilibili.com/xlive/web-ucenter/user/MedalWall"
        params = {"target_id": uid}
        bilibili = config.functions.get("bilibili")
        cookie = bilibili.get("cookie") if bilibili else None
        if not bilibili or not cookie:
            raise ValueError("cookie is None")
        headers = {"cookie": cookie}
        async with get_running(Adapter).session.get(url, params=params, headers=headers) as resp:
            result = await resp.json()
        return result["data"]["list"]
    except (KeyError, IndexError, asyncio.TimeoutError) as e:
        logger.warning(f"Error in get_medals({uid}): {e}")
        return []


def format_color(color: int) -> str:
    return f"#{color:06X}"


def format_vtb_info(info: dict, medal_dict: dict) -> dict:
    name = info["uname"]
    uid = info["mid"]
    medal = {}
    if name in medal_dict:
        medal_info = medal_dict[name]["medal_info"]
        medal = {
            "name": medal_info["medal_name"],
            "level": medal_info["level"],
            "color_border": format_color(medal_info["medal_color_border"]),
            "color_start": format_color(medal_info["medal_color_start"]),
            "color_end": format_color(medal_info["medal_color_end"]),
        }
    return {"name": name, "uid": uid, "medal": medal}


async def get_reply(name: str) -> Union[str, bytes]:
    uid = int(name) if name.isdigit() else await get_uid_by_name(name)
    user_info = await get_user_info(uid)
    if not user_info:
        return "获取用户信息失败，请检查名称或稍后再试"

    vtb_list = await get_vtb_list()
    if not vtb_list:
        return "获取vtb列表失败，请稍后再试"

    try:
        medals = await get_medals(uid)
    except ValueError:
        return "bilibili cookie未配置！"
    medal_dict = {medal["target_name"]: medal for medal in medals}

    vtb_dict = {info["mid"]: info for info in vtb_list}
    vtbs = [
        info for uid, info in vtb_dict.items() if uid in user_info.get("attentions", [])
    ]
    vtbs = [format_vtb_info(info, medal_dict) for info in vtbs]

    follows_num = int(user_info["attention"])
    vtbs_num = len(vtbs)
    percent = vtbs_num / follows_num * 100 if follows_num else 0
    result = {
        "name": user_info["name"],
        "uid": user_info["mid"],
        "face": user_info["face"],
        "fans": user_info["fans"],
        "follows": user_info["attention"],
        "percent": f"{percent:.2f}% ({vtbs_num}/{follows_num})",
        "vtbs": vtbs,
    }
    template = env.get_template("info.html")
    content = await template.render_async(info=result)
    return await html_to_pic(content, wait=0, viewport={"width": 100, "height": 100})
