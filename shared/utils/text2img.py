import re
import matplotlib
from io import BytesIO
from pathlib import Path
from jinja2 import Template
from jinja2 import Template
from datetime import datetime
from markdown_it import MarkdownIt
from matplotlib import pyplot as plt
from mdit_py_plugins.dollarmath import dollarmath_plugin

from kayaku import create
from graiax.text2img.playwright.renderer import BuiltinCSS
from graiax.text2img.playwright.plugins.code.highlighter import Highlighter
from graiax.text2img.playwright import HTMLRenderer, MarkdownConverter, PageOption, ScreenshotOption

from shared.utils.font import fill_font
from shared.models.config import GlobalConfig

proxy = create(GlobalConfig).proxy


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


footer = (
    '<style>.footer{box-sizing:border-box;position:absolute;left:0;width:100%;background:#eee;'
    'padding:50px 40px;margin-top:50px;font-size:0.85rem;color:#6b6b6b;}'
    '.footer p{margin:5px auto;}</style>'
    f'<div class="footer"><p>由 SAGIRI-BOT 生成</p><p>{datetime.now().strftime("%Y/%m/%d %p %I:%M:%S")}</p></div>'
)

md_converter = MarkdownConverter()


async def html2img(
    html: str, 
    page_option: dict | None = None, 
    extra_screenshot_option: dict | None = None, 
    use_proxy: bool = False, 
    with_footer: bool = True
) -> bytes:
    if with_footer:
        html += footer
    page_option = page_option or {"viewport": {"width": 1000, "height": 10}, "device_scale_factor": 1.5}
    if use_proxy and proxy:
        page_option["proxy"] = {"server": proxy}
    extra_screenshot_option = extra_screenshot_option or {"type": "jpeg", "quality": 80, "scale": "device"}
    return await HTMLRenderer(
        page_option=PageOption(device_scale_factor=1.5),
        screenshot_option=ScreenshotOption(type='jpeg', quality=80, full_page=True, scale='device'),
        css=(
            BuiltinCSS.reset,
            BuiltinCSS.github,
            BuiltinCSS.one_dark,
            BuiltinCSS.container,
            "body {padding: 0 !important}",
            "@font-face{font-family:'harmo';font-weight:300;"
            "src:url('http://static.graiax/fonts/HarmonyOS_Sans_SC_Light.ttf') format('truetype');}"
            "@font-face{font-family:'harmo';font-weight:400;"
            "src:url('http://static.graiax/fonts/HarmonyOS_Sans_SC_Regular.ttf') format('truetype');}"
            "@font-face{font-family:'harmo';font-weight:500;"
            "src:url('http://static.graiax/fonts/HarmonyOS_Sans_SC_Medium.ttf') format('truetype');}"
            "@font-face{font-family:'harmo';font-weight:600;"
            "src:url('http://static.graiax/fonts/HarmonyOS_Sans_SC_Bold.ttf') format('truetype');}"
            "*{font-family:'harmo',sans-serif}",
        ),
        page_modifiers=[
            lambda page: page.route(lambda url: bool(re.match('^http://static.graiax/fonts/(.+)$', url)), fill_font)
        ],
    ).render(
        html,
        extra_page_option=PageOption(**page_option),
        extra_screenshot_option=ScreenshotOption(**extra_screenshot_option),
    )


async def md2img(
    markdown: str, 
    page_option: dict | None = None, 
    extra_screenshot_option: dict | None = None, 
    use_proxy: bool = False,
    with_footer: bool = True
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
    return await html2img(res, page_option, extra_screenshot_option, use_proxy, with_footer)


async def template2img(
    template: str | Template | Path,
    params: dict,
    page_option: dict | None = None,
    extra_screenshot_option: dict | None = None,
    use_proxy: bool = False,
    with_footer: bool = True
) -> bytes:
    if isinstance(template, str):
        template = Template(template)
    elif isinstance(template, Path):
        if not template.is_file():
            raise ValueError("Path for template is not a file!") 
        template = Template(template.read_text(encoding="utf-8"))
    return await html2img(template.render(params), page_option, extra_screenshot_option, use_proxy, with_footer)
