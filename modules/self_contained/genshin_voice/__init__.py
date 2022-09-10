import aiohttp

from graia.saya import Channel
from graia.ariadne import Ariadne
from graia.ariadne.model import Group
from graiax.silkcoder import async_encode
from graia.ariadne.message.parser.twilight import Twilight, RegexMatch, WildcardMatch, RegexResult

from graia.ariadne.message.element import Voice
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.event.message import GroupMessage
from graia.saya.builtins.broadcast import ListenerSchema

from shared.utils.module_related import get_command
from shared.utils.control import FrequencyLimit, Function, BlackListControl, UserCalledCountControl

channel = Channel.current()
channel.name("GenshinVoice")
channel.author("SAGIRI-kawaii")

valid_characters = {
    '派蒙', '凯亚', '安柏', '丽莎', '琴', '香菱', '枫原万叶', '迪卢克', '温迪', '可莉', '早柚', '托马', '芭芭拉', '优菈', '云堇',
    '钟离', '魈', '凝光', '雷电将军', '北斗', '甘雨', '七七', '刻晴', '神里绫华', '戴因斯雷布', '雷泽', '神里绫人', '罗莎莉亚',
    '阿贝多', '八重神子', '宵宫', '荒泷一斗', '九条裟罗', '夜兰', '珊瑚宫心海', '五郎', '散兵', '女士', '达达利亚', '莫娜', '班尼特',
    '申鹤', '行秋', '烟绯', '久岐忍', '辛焱', '砂糖', '胡桃', '重云', '菲谢尔', '诺艾尔', '迪奥娜', '鹿野院平藏'
}
url = "http://233366.proxy.nscc-gz.cn:8888/?text={content}&speaker={speaker}"


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight([
                get_command(__file__, channel.module),
                RegexMatch(".+说") @ "speaker",
                WildcardMatch() @ "content"
            ])
        ],
        decorators=[
            FrequencyLimit.require("ill", 1),
            Function.require(channel.module, notice=True),
            BlackListControl.enable(),
            UserCalledCountControl.add(UserCalledCountControl.FUNCTIONS),
        ],
    )
)
async def ill(app: Ariadne, group: Group, speaker: RegexResult, content: RegexResult):
    speaker = speaker.result.display[2:-1].strip()
    content = content.result.display.strip()
    if speaker not in valid_characters:
        return await app.send_group_message(
            group, MessageChain(f"不支持的角色！目前支持的角色有：{'、'.join(valid_characters)}")
        )
    async with aiohttp.ClientSession() as session:
        async with session.get(url.format(content=content, speaker=speaker)) as resp:
            await app.send_group_message(
                group, MessageChain(Voice(data_bytes=await async_encode(await resp.read(), ios_adaptive=True)))
            )
