import base64
import traceback
import re
import time
import aiohttp
from creart import create
from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.chain import MessageChain, Image, Source, Plain, At, Quote
from graia.ariadne.event.message import Group, GroupMessage, Member
from graia.ariadne.message.parser.twilight import (
    Twilight,
    FullMatch,
    WildcardMatch,
    RegexResult,
    ArgumentMatch,
    ArgResult,
    RegexMatch
)

from shared.models.config import GlobalConfig
from shared.utils.image import get_user_avatar
from shared.utils.control import (
    FrequencyLimit,
    Function,
    BlackListControl,
    UserCalledCountControl,
    Distribute
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
                RegexMatch("-N=\[.+\]", optional=True) @ "negative_prompt",
                WildcardMatch().flags(re.DOTALL) @ "keywords"
            ])
        ],
        decorators=[
            Distribute.distribute(),
            FrequencyLimit.require("ai_t2i", 10),
            UserCalledCountControl.add(UserCalledCountControl.FUNCTIONS),
            Function.require(channel.module, notice=True),
            BlackListControl.enable(),
        ]
    )
)
async def ai_t2i(
    app: Ariadne,
    group: Group,
    member: Member,
    source: Source,
    width: ArgResult,
    height: ArgResult,
    steps: ArgResult,
    n_iter: ArgResult,
    cfg_scale: ArgResult,
    seed: ArgResult,
    negative_prompt: RegexResult,
    keywords: RegexResult
):
    global running
    if running:
        return await app.send_group_message(group, "running, try again later.")
    if member.id == 80000000:
        return await app.send_group_message(group, "不许匿名，你是不是想干坏事？")
    url = "http://localhost:7861/v1/txt2img"
    width = int(width.result.display) if width.matched and width.result.display.isnumeric() and int(width.result.display) % 24 == 0 else 512
    height = int(height.result.display) if height.matched and height.result.display.isnumeric() and int(height.result.display) % 24 == 0 else 512
    steps = int(steps.result.display) if steps.matched and steps.result.display.isnumeric() else 20
    n_iter = int(n_iter.result.display) if n_iter.matched and n_iter.result.display.isnumeric() else 1
    cfg_scale = int(cfg_scale.result.display) if cfg_scale.matched and cfg_scale.result.display.isnumeric() else 7
    seed = int(seed.result.display) if seed.matched and seed.result.display.isnumeric() else -1
    print(width, height, steps, n_iter)
    running = True
    st = time.time()
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url,
                headers={"Content-Type": "application/json", "accept": "application/json"},
                json={
                    "txt2imgreq": {
                        "prompt": keywords.result.display,
                        "negative_prompt": "lowers, bad anatomy, bad hands, text, error, missing fingers, "
                                           "extra digit, fewer digits, cropped, worst quality, low quality, "
                                           "normal quality, jpeg artfacts, signature, watermark, username, blurry, "
                                           "bad feet, multiple breasts, (mutated hands and fingers:1.5 ), (long body "
                                           ":1.3), (mutation, poorly drawn :1.2) , black-white, bad anatomy, "
                                           "liquid body, liquid tongue, disfigured, malformed, mutated, anatomical "
                                           "nonsense, text font ui, error, malformed hands, long neck, blurred, "
                                           "lowers, lowres, bad anatomy, bad proportions, bad shadow, uncoordinated "
                                           "body, unnatural body, fused breasts, bad breasts, huge breasts, "
                                           "poorly drawn breasts, extra breasts, liquid breasts, heavy breasts, "
                                           "missing breasts, huge haunch, huge thighs, huge calf, bad hands, "
                                           "fused hand, missing hand, disappearing arms, disappearing thigh, "
                                           "disappearing calf, disappearing legs, fused ears, bad ears, poorly drawn "
                                           "ears, extra ears, liquid ears, heavy ears, missing ears, fused animal "
                                           "ears, bad animal ears, poorly drawn animal ears, extra animal ears, "
                                           "liquid animal ears, heavy animal ears, missing animal ears, text, ui, "
                                           "error, missing fingers, missing limb, fused fingers, one hand with more "
                                           "than 5 fingers, one hand with less than 5 fingers, one hand with more "
                                           "than 5 digit, one hand with less than 5 digit, extra digit, fewer digits, "
                                           "fused digit, missing digit, bad digit, liquid digit, colorful tongue, "
                                           "black tongue, cropped, watermark, username, blurry, JPEG artifacts, "
                                           "signature, 3D, 3D game, 3D game scene, 3D character, malformed feet, "
                                           "extra feet, bad feet, poorly drawn feet, fused feet, missing feet, "
                                           "extra shoes, bad shoes, fused shoes, more than two shoes, poorly drawn "
                                           "shoes, bad gloves, poorly drawn gloves, fused gloves, bad cum, "
                                           "poorly drawn cum, fused cum, bad hairs, poorly drawn hairs, fused hairs, "
                                           "big muscles, ugly, bad face, fused face, poorly drawn face, cloned face, "
                                           "big face, long face, bad eyes, fused eyes poorly drawn eyes, extra eyes, "
                                           "malformed limbs, more than 2 nipples, missing nipples, different nipples, "
                                           "fused nipples, bad nipples, poorly drawn nipples, black nipples, "
                                           "colorful nipples, gross proportions. short arm, (((missing arms))), "
                                           "missing thighs, missing calf, missing legs, mutation, duplicate, morbid, "
                                           "mutilated, poorly drawn hands, more than 1 left hand, more than 1 right "
                                           "hand, deformed, (blurry), disfigured, missing legs, extra arms, "
                                           "extra thighs, more than 2 thighs, extra calf, fused calf, extra legs, "
                                           "bad knee, extra knee, more than 2 legs, bad tails, bad mouth, "
                                           "fused mouth, poorly drawn mouth, bad tongue, tongue within mouth, "
                                           "too long tongue, black tongue, big mouth, cracked mouth, bad mouth, "
                                           "dirty face, dirty teeth, dirty pantie, fused pantie, poorly drawn pantie, "
                                           "fused cloth, poorly drawn cloth, bad pantie, yellow teeth, thick lips, "
                                           "bad cameltoe, colorful cameltoe, bad asshole, poorly drawn asshole, "
                                           "fused asshole, missing asshole, bad anus, bad pussy, bad crotch, "
                                           "bad crotch seam, fused anus, fused pussy, fused anus, fused crotch, "
                                           "poorly drawn crotch, fused seam, poorly drawn anus, poorly drawn pussy, "
                                           "poorly drawn crotch, poorly drawn crotch seam, bad thigh gap, "
                                           "missing thigh gap, fused thigh gap, liquid thigh gap, poorly drawn thigh "
                                           "gap, poorly drawn anus, bad collarbone, fused collarbone, "
                                           "missing collarbone, liquid collarbone, strong girl, obesity, "
                                           "worst quality, low quality, normal quality, liquid tentacles, "
                                           "bad tentacles, poorly drawn tentacles, split tentacles, fused tentacles, "
                                           "missing clit, bad clit, fused clit, colorful clit, black clit, "
                                           "liquid clit, QR code, bar code, censored, safety panties, "
                                           "safety knickers, beard, furry ,pony, pubic hair, mosaic, excrement, "
                                           "faeces, shit, futa, testis" + (f",{negative_prompt.result.display[4:-1]}"
                                            if negative_prompt.matched else ""),
                        "prompt_style": "None",
                        "prompt_style2": "None",
                        "steps": steps if steps <= 150 else 20,
                        "sampler_index": 0,
                        "restore_faces": False,
                        "tiling": False,
                        "n_iter": (n_iter if n_iter <= 9 else 1),
                        "batch_size": 1,
                        "cfg_scale": cfg_scale,
                        "seed": seed,
                        "subseed": -1,
                        "subseed_strength": 0,
                        "seed_resize_from_h": 0,
                        "seed_resize_from_w": 0,
                        "height": height,
                        "width": width,
                        "enable_hr": False,
                        "scale_latent": True,
                        "denoising_strength": 0.7
                    }
                }
            ) as resp:
                data = await resp.json()
                img_b64 = data["images"][0]
                seed = data["seed"]
                await app.send_group_message(
                    group,
                    MessageChain([f"use: {int(time.time() - st)}s\nSeed: {seed}\n", Image(base64=img_b64)]),
                    quote=source
                )
                running = False
    except Exception as e:
        print(traceback.format_exc())
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
                ArgumentMatch("-q", "--qq", optional=True) @ "target",
                WildcardMatch().flags(re.DOTALL) @ "message"
            ])
        ],
        decorators=[
            Distribute.distribute(),
            FrequencyLimit.require("ai_i2i", 10),
            Function.require(channel.module, notice=True),
            BlackListControl.enable(),
            UserCalledCountControl.add(UserCalledCountControl.FUNCTIONS),
        ]
    )
)
async def ai_i2i(
    app: Ariadne,
    group: Group,
    member: Member,
    source: Source,
    quote: Quote | None,
    width: ArgResult,
    height: ArgResult,
    steps: ArgResult,
    n_iter: ArgResult,
    target: ArgResult,
    message: RegexResult
):
    global running
    if running:
        return await app.send_group_message(group, "running, try again later.")
    if member.id == 80000000:
        return await app.send_group_message(group, "不许匿名，你是不是想干坏事？")
    url = "http://localhost:7861/v1/img2img"
    width = int(width.result.display) if width.matched and width.result.display.isnumeric() and int(width.result.display) % 24 == 0 else 512
    height = int(height.result.display) if height.matched and height.result.display.isnumeric() and int(height.result.display) % 24 == 0 else 512
    steps = int(steps.result.display) if steps.matched and steps.result.display.isnumeric() else 20
    n_iter = int(n_iter.result.display) if n_iter.matched and n_iter.result.display.isnumeric() else 1
    print(width, height, steps, n_iter)
    if message.result.get(Image):
        image_bytes = await message.result[Image][0].get_bytes()
    elif quote and (msg := await app.get_message_from_id(quote.origin[Source][0])).message_chain.get(Image):
        image_bytes = await msg.message_chain[Image][0].get_bytes()
    elif target.matched:
        image_bytes = await get_user_avatar(target.result.strip())
    elif message.result.get(At):
        image_bytes = await get_user_avatar(message.result[At][0].target)
    else:
        return
    keywords = "".join(i.text for i in message.result[Plain]).strip()
    running = True
    st = time.time()
    img_b64 = base64.b64encode(image_bytes).decode('utf8')
    data = {
        "img2imgreq": {
            "prompt": keywords,
            "negative_prompt": "lowers, bad anatomy, bad hands, text, error, missing fingers, "
                               "extra digit, fewer digits, cropped, worst quality, low quality, "
                               "normal quality, jpeg artfacts, signature, watermark, username, blurry, "
                               "bad feet",
            "prompt_style": "None",
            "prompt_style2": "None",
            "init_img_with_mask": None,
            "init_mask": None,
            "mask_mode": None,
            "init_img": img_b64,
            "steps": steps if steps <= 150 else 20,
            "sampler_index": 0,
            "mask_blur": 0,
            "inpainting_fill": 0,
            "restore_faces": False,
            "tiling": False,
            "n_iter": (n_iter if n_iter <= 9 else 1),
            "batch_size": 1,
            "cfg_scale": 7,
            "seed": -1,
            "subseed": -1,
            "denoising_strength": 0.7,
            "seed_resize_from_h": 0,
            "seed_resize_from_w": 0,
            "height": height,
            "width": width,
            "resize_mode": 0,
            "upscaler_index": 0,
            "upscale_overlap": 0,
            "inpaint_full_res": False,
            "inpainting_mask_invert": 0,
        }
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url,
                headers={"Content-Type": "application/json", "accept": "application/json"},
                json=data
            ) as resp:
                data = await resp.json()
                img_b64 = data["images"][0]
                seed = data["seed"]
                await app.send_group_message(
                    group,
                    MessageChain([f"use: {int(time.time() - st)}s\nSeed: {seed}\n", Image(base64=img_b64)]),
                    quote=source
                )
                running = False
    except Exception as e:
        print(traceback.format_exc())
        running = False
        raise e
