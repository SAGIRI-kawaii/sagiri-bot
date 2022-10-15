import re
import time
import base64

from creart import create
from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import Group, GroupMessage
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.chain import MessageChain, Image, Source, Plain, At, Quote
from graia.ariadne.message.parser.twilight import (
    Twilight,
    FullMatch,
    WildcardMatch,
    RegexResult,
    ArgumentMatch,
    ArgResult,
    RegexMatch
)

from .requests import sd_req
from shared.models.config import GlobalConfig
from shared.utils.image import get_user_avatar
from shared.utils.type import parse_match_type
from .models import DEFAULT_NEGATIVE_PROMPT, Text2Image, Image2Image
from shared.utils.control import (
    FrequencyLimit,
    Function,
    BlackListControl,
    UserCalledCountControl,
    Distribute,
    Config,
    Anonymous
)

saya = create(Saya)
channel = Channel.current()

channel.name("StableDiffusion")
channel.author("SAGIRI-kawaii")
config = create(GlobalConfig)

running = False


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight([
                FullMatch("/ait2i"),
                ArgumentMatch("-w", "--width", optional=True) @ "width",
                ArgumentMatch("-h", "--height", optional=True) @ "height",
                ArgumentMatch("-s", "--steps", optional=True) @ "steps",
                ArgumentMatch("-n", "--n_iter", optional=True) @ "n_iter",
                ArgumentMatch("-c", "--cfg_scale", optional=True) @ "cfg_scale",
                ArgumentMatch("-S", "--seed", optional=True) @ "seed",
                ArgumentMatch("-ss", "-sS", "--subseed", optional=True) @ "subseed",
                ArgumentMatch("-d", "--denoising_strength", optional=True) @ "denoising_strength",
                RegexMatch(r"-N=\[.+\]", optional=True) @ "negative_prompt",
                WildcardMatch().flags(re.DOTALL) @ "keywords"
            ])
        ],
        decorators=[
            Distribute.distribute(),
            FrequencyLimit.require("ai_t2i", 10),
            UserCalledCountControl.add(UserCalledCountControl.FUNCTIONS),
            Function.require(channel.module, notice=True),
            BlackListControl.enable(),
            Config.require("functions.stable_diffusion_api"),
            Anonymous.block()
        ]
    )
)
async def ai_t2i(
    app: Ariadne,
    group: Group,
    source: Source,
    width: ArgResult,
    height: ArgResult,
    steps: ArgResult,
    n_iter: ArgResult,
    cfg_scale: ArgResult,
    seed: ArgResult,
    subseed: ArgResult,
    denoising_strength: ArgResult,
    negative_prompt: RegexResult,
    keywords: RegexResult,
):
    global running
    if running:
        return await app.send_group_message(group, "running, try again later.")
    width = parse_match_type(width, int, 512)
    height = parse_match_type(height, int, 512)
    steps = parse_match_type(steps, int, 20)
    n_iter = parse_match_type(n_iter, int, 1)
    cfg_scale = parse_match_type(cfg_scale, float, 12)
    seed = parse_match_type(seed, int, -1)
    subseed = parse_match_type(subseed, int, -1)
    denoising_strength = parse_match_type(denoising_strength, int, 0.3)
    negative_prompt = negative_prompt.result.display[4:-1] if negative_prompt.matched else ""
    print(width, height, steps, n_iter, cfg_scale, seed, subseed, denoising_strength)
    keywords = "".join(i.text for i in keywords.result[Plain]).strip()
    running = True
    st = time.time()
    data = Text2Image(
        prompt=keywords,
        negative_prompt=DEFAULT_NEGATIVE_PROMPT + negative_prompt,
        steps=steps if steps <= 150 else 20,
        n_iter=n_iter if n_iter <= 9 else 1,
        cfg_scale=cfg_scale if 0 <= cfg_scale <= 30 else 12,
        seed=seed,
        subseed=subseed,
        height=height,
        width=width,
        denoising_strength=denoising_strength
    )
    try:
        data = await sd_req(data)
        img_b64 = data["images"][0]
        seed = data["seed"]
        await app.send_group_message(
            group,
            MessageChain([f"use: {int(time.time() - st)}s\nSeed: {seed}\n", Image(base64=img_b64)]),
            quote=source
        )
        running = False
    except Exception as e:
        running = False
        raise e


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight([
                FullMatch("/aii2i"),
                ArgumentMatch("-w", "--width", optional=True) @ "width",
                ArgumentMatch("-h", "--height", optional=True) @ "height",
                ArgumentMatch("-s", "--steps", optional=True) @ "steps",
                ArgumentMatch("-n", "--n_iter", optional=True) @ "n_iter",
                ArgumentMatch("-c", "--cfg_scale", optional=True) @ "cfg_scale",
                ArgumentMatch("-S", "--seed", optional=True) @ "seed",
                ArgumentMatch("-ss", "-sS", "--subseed", optional=True) @ "subseed",
                ArgumentMatch("-d", "--denoising_strength", optional=True) @ "denoising_strength",
                ArgumentMatch("-q", "--qq", optional=True) @ "target",
                RegexMatch(r"-N=\[.+\]", optional=True) @ "negative_prompt",
                WildcardMatch().flags(re.DOTALL) @ "message"
            ])
        ],
        decorators=[
            Distribute.distribute(),
            FrequencyLimit.require("ai_i2i", 10),
            Function.require(channel.module, notice=True),
            BlackListControl.enable(),
            UserCalledCountControl.add(UserCalledCountControl.FUNCTIONS),
            Config.require("functions.stable_diffusion_api"),
            Anonymous.block()
        ]
    )
)
async def ai_i2i(
    app: Ariadne,
    group: Group,
    source: Source,
    quote: Quote | None,
    width: ArgResult,
    height: ArgResult,
    steps: ArgResult,
    n_iter: ArgResult,
    cfg_scale: ArgResult,
    seed: ArgResult,
    subseed: ArgResult,
    denoising_strength: ArgResult,
    target: ArgResult,
    negative_prompt: RegexResult,
    message: RegexResult,
):
    global running
    if running:
        return await app.send_group_message(group, "running, try again later.")
    width = parse_match_type(width, int, 512)
    height = parse_match_type(height, int, 512)
    steps = parse_match_type(steps, int, 20)
    n_iter = parse_match_type(n_iter, int, 1)
    cfg_scale = parse_match_type(cfg_scale, float, 12)
    seed = parse_match_type(seed, int, -1)
    subseed = parse_match_type(subseed, int, -1)
    denoising_strength = parse_match_type(denoising_strength, int, 0.3)
    negative_prompt = negative_prompt.result.display[4:-1] if negative_prompt.matched else ""
    print(width, height, steps, n_iter, cfg_scale, seed, subseed, denoising_strength)
    if message.result.get(Image):
        image_bytes = await message.result[Image][0].get_bytes()
    elif quote and (msg := await app.get_message_from_id(quote.origin[Source][0], group)).message_chain.get(Image):
        image_bytes = await msg.message_chain[Image][0].get_bytes()
    elif target.matched:
        image_bytes = await get_user_avatar(target.result.display.strip())
    elif message.result.get(At):
        image_bytes = await get_user_avatar(message.result[At][0].target)
    else:
        return
    keywords = "".join(i.text for i in message.result[Plain]).strip()
    running = True
    st = time.time()
    img_b64 = base64.b64encode(image_bytes).decode('utf8')
    data = Image2Image(
        prompt=keywords,
        negative_prompt=DEFAULT_NEGATIVE_PROMPT + negative_prompt,
        init_img=img_b64,
        steps=steps if steps <= 150 else 20,
        n_iter=n_iter if n_iter <= 9 else 1,
        cfg_scale=cfg_scale if 0 <= cfg_scale <= 30 else 12,
        seed=seed,
        subseed=subseed,
        height=height,
        width=width,
        denoising_strength=denoising_strength
    )
    try:
        data = await sd_req(data)
        img_b64 = data["images"][0]
        seed = data["seed"]
        await app.send_group_message(
            group,
            MessageChain([f"use: {int(time.time() - st)}s\nSeed: {seed}\n", Image(base64=img_b64)]),
            quote=source
        )
        running = False
    except Exception as e:
        running = False
        raise e
