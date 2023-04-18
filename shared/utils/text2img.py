import re
import matplotlib
from io import BytesIO
from pathlib import Path
from jinja2 import Template
from base64 import b64encode
from markdown_it import MarkdownIt
from matplotlib import pyplot as plt
from mdit_py_plugins.dollarmath import dollarmath_plugin

from creart import create
from graia.ariadne.message.chain import MessageChain
from graiax.text2img.playwright.renderer import BuiltinCSS
from graiax.text2img.playwright.plugins.code.highlighter import Highlighter
from graiax.text2img.playwright import HTMLRenderer, MarkdownConverter, PageOption, ScreenshotOption
from graia.ariadne.message.element import Plain, Image, Face, At, AtAll, MarketFace, Dice, MusicShare, Forward, File

from core import Sagiri

config = create(Sagiri).config
proxy = config.proxy if config.proxy != "proxy" else None


def tex2svg(formula):
    formula = re.sub(r"\\pmod", r"\ mod\ ", formula)
    formula = re.sub(r"\\bmod", r"\ mod\ ", formula)
    matplotlib.use('agg')
    plt.rc("mathtext", fontset="cm")
    fig = plt.figure(figsize=(0.01, 0.01))
    fig.text(0, 0, r"${}$".format(formula), fontsize=20)
    output = BytesIO()
    fig.savefig(
        output,
        dpi=30,
        transparent=True,
        format="svg",
        bbox_inches="tight",
        pad_inches=0.0,
    )
    plt.close(fig)
    output.seek(0)
    xml_code = output.read().decode("utf-8")
    svg_start = xml_code.index("<svg ")
    svg_code = xml_code[svg_start:]
    svg_code = re.sub(r"<metadata>.*</metadata>", "", svg_code, flags=re.DOTALL)
    svg_code = re.sub(r' width="[^"]+"', "", svg_code)
    height_match = re.search(r'height="([\d.]+)pt"', svg_code)
    if height_match:
        height = float(height_match.group(1))
        new_height = height / 20  # conversion from pt to em
        svg_code = re.sub(r'height="[\d.]+pt"', f'height="{new_height}em"', svg_code)
    copy_code = f"<span style='font-size: 0px'>{formula}</span>"
    return f"{copy_code}{svg_code}"


async def html2img(
    html: str, page_option: dict | None = None, extra_screenshot_option: dict | None = None, use_proxy: bool = False
) -> bytes:
    page_option = page_option or {"viewport": {"width": 1000, "height": 10}, "device_scale_factor": 1.5}
    if use_proxy and proxy:
        page_option["proxy"] = {"server": proxy}
    extra_screenshot_option = extra_screenshot_option or {"type": "jpeg", "quality": 80, "scale": "device"}
    return await HTMLRenderer(
        css=(
            BuiltinCSS.reset,
            BuiltinCSS.github,
            BuiltinCSS.one_dark,
            BuiltinCSS.container,
            "body {padding: 0 !important}"
        )
    ).render(
        html,
        extra_page_option=PageOption(**page_option),
        extra_screenshot_option=ScreenshotOption(**extra_screenshot_option),
    )


async def md2img(
    markdown: str, page_option: dict | None = None, extra_screenshot_option: dict | None = None, use_proxy: bool = False
) -> bytes:
    md = MarkdownIt("gfm-like", {"highlight": Highlighter()}).use(
        dollarmath_plugin,
        allow_labels=False,
        allow_space=True,
        allow_digits=False,
        double_inline=True,
        renderer=tex2svg
    ).enable("table")
    res = MarkdownConverter(md).convert(markdown)
    return await html2img(res, page_option, extra_screenshot_option, use_proxy)


async def template2img(
    template: str | Template | Path,
    params: dict,
    page_option: dict | None = None,
    extra_screenshot_option: dict | None = None,
    use_proxy: bool = False
) -> bytes:
    if isinstance(template, str):
        template = Template(template)
    elif isinstance(template, Path):
        if not template.is_file():
            raise ValueError("Path for template is not a file!") 
        template = Template(template.read_text(encoding="utf-8"))
    return await html2img(template.render(params), page_option, extra_screenshot_option, use_proxy)


async def messagechain2img(
    message: MessageChain,
    img_single_line: bool = False,
    page_option: dict | None = None,
    extra_screenshot_option: dict | None = None
) -> bytes:
    html = ""
    for i in message.content:
        if isinstance(i, Plain):
            html += i.text.replace("\n", "<br>")
        elif isinstance(i, Image):
            if img_single_line:
                html += "<br>"
            html += f'<img src="data:image/png;base64,{b64encode(await i.get_bytes()).decode("ascii")}" />'
            if img_single_line:
                html += "<br>"
        elif isinstance(i, (Face, MarketFace)):
            html += f"【表情：{i.face_id}】"
        elif isinstance(i, At):
            html += f"@{i.representation}"
        elif isinstance(i, AtAll):
            html += "@全体成员"
        elif isinstance(i, Dice):
            html += f"【骰子：{i.value}】"
        elif isinstance(i, MusicShare):
            html += f"【音乐分享：{i.title}】"
        elif isinstance(i, Forward):
            html += "【转发消息】"
        elif isinstance(i, File):
            html += f"【文件：{i.name}】"
    return await html2img(html.strip("<br>"), page_option, extra_screenshot_option)