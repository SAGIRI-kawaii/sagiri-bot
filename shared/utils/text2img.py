from pathlib import Path
from jinja2 import Template
from markdown_it import MarkdownIt
from mdit_py_plugins.dollarmath import dollarmath_plugin

from creart import create
from graiax.text2img.playwright.renderer import BuiltinCSS
from graiax.text2img.playwright.plugins.code.highlighter import Highlighter
from graiax.text2img.playwright import HTMLRenderer, MarkdownConverter, PageOption, ScreenshotOption

from core import Sagiri

config = create(Sagiri).config
proxy = config.proxy if config.proxy != "proxy" else None


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
        allow_labels=True,
        allow_space=True,
        allow_digits=True,
        double_inline=True,
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
