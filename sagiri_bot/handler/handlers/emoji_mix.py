from loguru import logger
from typing import Union, Tuple, List, Optional

from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.ariadne import get_running
from graia.ariadne.adapter import Adapter
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Image, Source
from graia.ariadne.message.parser.twilight import Twilight
from graia.ariadne.event.message import Group, GroupMessage
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.parser.twilight import RegexMatch, FullMatch, RegexResult

from sagiri_bot.core.app_core import AppCore
from sagiri_bot.control import FrequencyLimit, Function, BlackListControl, UserCalledCountControl

saya = Saya.current()
channel = Channel.current()

channel.name("EmojiMix")
channel.author("SAGIRI-kawaii")
channel.author("from: MeetWq")
channel.description("一个生成emoji融合图的插件，发送 '{emoji1}+{emoji2}' 即可")

EmojiData = Tuple[List[int], str, str]
API = 'https://www.gstatic.com/android/keyboard/emojikitchen/'
proxy = AppCore.get_core_instance().get_config().proxy


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight([
                RegexMatch(u"[\u200d-\U0001fab5]") @ "emoji1", FullMatch("+"),
                RegexMatch(u"[\u200d-\U0001fab5]") @ "emoji2"]
            )
        ],
        decorators=[
            FrequencyLimit.require("emoji_mix", 2),
            Function.require(channel.module, notice=True),
            BlackListControl.enable(),
            UserCalledCountControl.add(UserCalledCountControl.FUNCTIONS)
        ]
    )
)
async def emoji_mix(app: Ariadne, message: MessageChain, group: Group, emoji1: RegexResult, emoji2: RegexResult):
    emoji1 = emoji1.result.asDisplay()
    emoji2 = emoji2.result.asDisplay()
    result = await mix_emoji(emoji1, emoji2)
    if isinstance(result, str):
        await app.sendGroupMessage(group, MessageChain(result), quote=message.getFirst(Source))
    elif isinstance(result, bytes):
        await app.sendGroupMessage(group, MessageChain([Image(data_bytes=result)]), quote=message.getFirst(Source))


def create_url(emoji1: EmojiData, emoji2: EmojiData) -> str:
    def emoji_code(emoji: EmojiData):
        return '-'.join(map(lambda c: f'u{c:x}', emoji[0]))

    u1 = emoji_code(emoji1)
    u2 = emoji_code(emoji2)
    return f'{API}{emoji1[2]}/{u1}/{u1}_{u2}.png'


async def mix_emoji(emoji_code1: str, emoji_code2: str) -> Union[str, bytes]:
    emoji1 = find_emoji(emoji_code1)
    emoji2 = find_emoji(emoji_code2)
    if not emoji1:
        return f'不支持的emoji：{emoji_code1}'
    if not emoji2:
        return f'不支持的emoji：{emoji_code2}'

    url1 = create_url(emoji1, emoji2)
    url2 = create_url(emoji2, emoji1)
    # logger.info(url1)
    # logger.info(url2)
    try:
        async with get_running(Adapter).session.get(url1, proxy=proxy) as resp:
            if resp.status == 200:
                return await resp.read()
        async with get_running(Adapter).session.get(url2, proxy=proxy) as resp:
            if resp.status == 200:
                return await resp.read()
        return '出错了，可能不支持该emoji组合'
    except:
        logger.exception("")
        return '下载出错，请稍后再试'


def find_emoji(emoji_code: str) -> Optional[EmojiData]:
    emoji_num = ord(emoji_code)
    for e in emojis:
        if emoji_num in e[0]:
            return e
    return None


emojis: List[EmojiData] = [
    ([128516], "grinning face with smiling eyes", "20201001"),
    ([128512], "grinning face", "20201001"),
    ([128578], "slightly smiling face", "20201001"),
    ([128579], "upside-down face", "20201001"),
    ([128521], "winking face", "20201001"),
    ([128522], "smiling face with smiling eyes", "20201001"),
    ([128518], "grinning squinting face", "20201001"),
    ([128515], "grinning face with big eyes", "20201001"),
    ([128513], "beaming face with smiling eyes", "20201001"),
    ([129315], "rolling on the floor laughing", "20201001"),
    ([128517], "grinning face with sweat", "20201001"),
    ([128514], "face with tears of joy", "20201001"),
    ([128519], "smiling face with halo", "20201001"),
    ([129392], "smiling face with hearts", "20201001"),
    ([128525], "smiling face with heart-eyes", "20201001"),
    ([128536], "face blowing a kiss", "20201001"),
    ([129321], "star-struck", "20201001"),
    ([128535], "kissing face", "20201001"),
    ([128538], "kissing face with closed eyes", "20201001"),
    ([128537], "kissing face with smiling eyes", "20201001"),
    ([128539], "face with tongue", "20201001"),
    ([128541], "squinting face with tongue", "20201001"),
    ([128523], "face savoring food", "20201001"),
    ([129394], "smiling face with tear", "20201001"),
    ([129297], "money-mouth face", "20201001"),
    ([128540], "winking face with tongue", "20201001"),
    ([129303], "smiling face with open hands hugs", "20201001"),
    ([129323], "shushing face quiet whisper", "20201001"),
    ([129300], "thinking face question hmmm", "20201001"),
    ([129325], "face with hand over mouth embarrassed", "20201001"),
    ([129320], "face with raised eyebrow question", "20201001"),
    ([129296], "zipper-mouth face", "20201001"),
    ([128528], "neutral face", "20201001"),
    ([128529], "expressionless face", "20201001"),
    ([128566], "face without mouth", "20201001"),
    ([129322], "zany face", "20201001"),
    ([128566, 8205, 127787, 65039], "face in clouds", "20210218"),
    ([128527], "smirking face suspicious", "20201001"),
    ([128530], "unamused face", "20201001"),
    ([128580], "face with rolling eyes", "20201001"),
    ([128556], "grimacing face", "20201001"),
    ([128558, 8205, 128168], "face exhaling", "20210218"),
    ([129317], "lying face", "20201001"),
    ([128524], "relieved face", "20201001"),
    ([128532], "pensive face", "20201001"),
    ([128554], "sleepy face", "20201001"),
    ([129316], "drooling face", "20201001"),
    ([128564], "sleeping face", "20201001"),
    ([128567], "face with medical mask", "20201001"),
    ([129298], "face with thermometer", "20201001"),
    ([129301], "face with head-bandage", "20201001"),
    ([129314], "nauseated face", "20201001"),
    ([129326], "face vomiting throw", "20201001"),
    ([129319], "sneezing face", "20201001"),
    ([129397], "hot face warm", "20201001"),
    ([129398], "cold face freezing ice", "20201001"),
    ([128565], "face with crossed-out eyes", "20201001"),
    ([129396], "woozy face drunk tipsy drug high", "20201001"),
    ([129327], "exploding head mindblow", "20201001"),
    ([129312], "cowboy hat face", "20201001"),
    ([129395], "partying face", "20201001"),
    ([129400], "disguised face", "20201001"),
    ([129488], "face with monocle glasses", "20201001"),
    ([128526], "smiling face with sunglasses", "20201001"),
    ([128533], "confused face", "20201001"),
    ([128543], "worried face", "20201001"),
    ([128577], "slightly frowning face", "20201001"),
    ([128558], "face with open mouth", "20201001"),
    ([128559], "hushed face", "20201001"),
    ([128562], "astonished face", "20201001"),
    ([129299], "nerd face glasses", "20201001"),
    ([128563], "flushed face", "20201001"),
    ([129402], "pleading face", "20201001"),
    ([128551], "anguished face", "20201001"),
    ([128552], "fearful face", "20201001"),
    ([128550], "frowning face with open mouth", "20201001"),
    ([128560], "anxious face with sweat", "20201001"),
    ([128549], "sad but relieved face", "20201001"),
    ([128557], "loudly crying face", "20201001"),
    ([128553], "weary face", "20201001"),
    ([128546], "crying face", "20201001"),
    ([128547], "persevering face", "20201001"),
    ([128544], "angry face", "20201001"),
    ([128531], "downcast face with sweat", "20201001"),
    ([128534], "confounded face", "20201001"),
    ([129324], "face with symbols on mouth", "20201001"),
    ([128542], "disappointed face", "20201001"),
    ([128555], "tired face", "20201001"),
    ([128548], "face with steam from nose", "20201001"),
    ([129393], "yawning face", "20201001"),
    ([128169], "pile of poo", "20201001"),
    ([128545], "pouting face", "20201001"),
    ([128561], "face screaming in fear", "20201001"),
    ([128127], "angry face with horns", "20201001"),
    ([128128], "skull", "20201001"),
    ([128125], "alien", "20201001"),
    ([128520], "smiling face with horns devil", "20201001"),
    ([129313], "clown face", "20201001"),
    ([128123], "ghost", "20201001"),
    ([129302], "robot", "20201001"),
    ([128175], "hundred points percent", "20201001"),
    ([128064], "eyes", "20201001"),
    ([127801], "rose flower", "20201001"),
    ([127804], "blossom flower", "20201001"),
    ([127799], "tulip flower", "20201001"),
    ([127797], "cactus", "20201001"),
    ([127821], "pineapple", "20201001"),
    ([127874], "birthday cake", "20201001"),
    ([127751], "sunset", "20210831"),
    ([129473], "cupcake muffin", "20201001"),
    ([127911], "headphone earphone", "20210521"),
    ([127800], "cherry blossom flower", "20210218"),
    ([129440], "microbe germ bacteria virus covid corona", "20201001"),
    ([128144], "bouquet flowers", "20201001"),
    ([127789], "hot dog food", "20201001"),
    ([128139], "kiss mark lips", "20201001"),
    ([127875], "jack-o-lantern pumpkin", "20201001"),
    ([129472], "cheese wedge", "20201001"),
    ([9749], "hot beverage coffee cup tea", "20201001"),
    ([127882], "confetti ball", "20201001"),
    ([127880], "balloon", "20201001"),
    ([9924], "snowman without snow", "20201001"),
    ([128142], "gem stone crystal diamond", "20201001"),
    ([127794], "evergreen tree", "20201001"),
    ([129410], "scorpion", "20210218"),
    ([128584], "see-no-evil monkey", "20201001"),
    ([128148], "broken heart", "20201001"),
    ([128140], "love letter heart", "20201001"),
    ([128152], "heart with arrow", "20201001"),
    ([128159], "heart decoration", "20201001"),
    ([128158], "revolving hearts", "20201001"),
    ([128147], "beating heart", "20201001"),
    ([128149], "two hearts", "20201001"),
    ([128151], "growing heart", "20201001"),
    ([129505], "orange heart", "20201001"),
    ([128155], "yellow heart", "20201001"),
    ([10084, 65039, 8205, 129657], "mending heart", "20210218"),
    ([128156], "purple heart", "20201001"),
    ([128154], "green heart", "20201001"),
    ([128153], "blue heart", "20201001"),
    ([129294], "brown heart", "20201001"),
    ([129293], "white heart", "20201001"),
    ([128420], "black heart", "20201001"),
    ([128150], "sparkling heart", "20201001"),
    ([128157], "heart with ribbon", "20201001"),
    ([127873], "wrapped-gift", "20211115"),
    ([129717], "wood", "20211115"),
    ([127942], "trophy", "20211115"),
    ([127838], "bread", "20210831"),
    ([128240], "newspaper", "20201001"),
    ([128302], "crystal ball", "20201001"),
    ([128081], "crown", "20201001"),
    ([128055], "pig face", "20201001"),
    ([129412], "unicorn", "20210831"),
    ([127771], "first quarter moon face", "20201001"),
    ([129420], "deer", "20201001"),
    ([129668], "magic wand", "20210521"),
    ([128171], "dizzy", "20201001"),
    ([128049], "meow cat face", "20201001"),
    ([129409], "lion", "20201001"),
    ([128293], "fire", "20201001"),
    ([128038], "bird", "20210831"),
    ([129415], "bat", "20201001"),
    ([129417], "owl", "20210831"),
    ([127752], "rainbow", "20201001"),
    ([128053], "monkey face", "20201001"),
    ([128029], "honeybee bumblebee wasp", "20201001"),
    ([128034], "turtle", "20201001"),
    ([128025], "octopus", "20201001"),
    ([129433], "llama alpaca", "20201001"),
    ([128016], "goat", "20210831"),
    ([128060], "panda", "20201001"),
    ([128040], "koala", "20201001"),
    ([129445], "sloth", "20201001"),
    ([128059], "bear", "20210831"),
    ([128048], "rabbit face", "20201001"),
    ([129428], "hedgehog", "20201001"),
    ([128054], "dog puppy", "20211115"),
    ([128041], "poodle dog", "20211115"),
    ([129437], "raccoon", "20211115"),
    ([128039], "penguin", "20211115"),
    ([128012], "snail", "20210218"),
    ([128045], "mouse face rat", "20201001"),
    ([128031], "fish", "20210831"),
    ([127757], "globe showing Europe-Africa", "20201001"),
    ([127774], "sun with face", "20201001"),
    ([127775], "glowing star", "20201001"),
    ([11088], "star", "20201001"),
    ([127772], "last quarter moon face", "20201001"),
    ([129361], "avocado", "20201001"),
    ([127820], "banana", "20211115"),
    ([127827], "strawberry", "20210831"),
    ([127819], "lemon", "20210521"),
    ([127818], "tangerine orange", "20211115"),
]
