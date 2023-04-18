import re
import base64

from meme_generator.meme import Meme

from graia.ariadne.message.element import Quote
from graia.broadcast.builtin.decorators import Depend
from graia.ariadne.message.parser.twilight import Twilight, UnionMatch, WildcardMatch, FullMatch, ElementMatch, ArgumentMatch


def gen_twilight(meme: Meme, with_help: bool = False) -> Twilight:
    if with_help:
        return Twilight([
            FullMatch("/"),
            UnionMatch(*meme.keywords),
            ArgumentMatch("-h", "--help", action="store_true") @ "help_wanted",
            WildcardMatch().flags(re.DOTALL)
        ])
    return Twilight([
        FullMatch("/"),
        UnionMatch(*meme.keywords),
        ArgumentMatch("-h", "--help", action="store_true", optional=True) @ "help_wanted",
        ElementMatch(Quote, optional=True) @ "quote",
        WildcardMatch().flags(re.DOTALL) @ "args"
    ])


def gen_depend(meme: Meme) -> Depend:
    def _():
        return meme
    return Depend(_)


async def gen_doc(meme: Meme, md_type: bool = True) -> str:
    return (
        f"## {meme.key}<br>"
        f"关键词：{'、'.join([f'/{i}' for i in meme.keywords])}<br>"
        f"需要图片数目：{meme.params_type.min_images}-{meme.params_type.max_images}<br>"
        f"需要文字数目：{meme.params_type.min_texts}-{meme.params_type.max_texts}<br>"
        f"预览：<img src=\"data:image/png;base64,{base64.b64encode((await meme.generate_preview()).getvalue())}\">"
    )
