from pathlib import Path
from jinja2 import Template

from graiax.text2img.playwright.renderer import BuiltinCSS
from graiax.text2img.playwright import HTMLRenderer, convert_md, PageOption, ScreenshotOption


async def html2img(
    html: str, page_option: dict | None = None, extra_screenshot_option: dict | None = None
) -> bytes:
    page_option = page_option or {"viewport": {"width": 1000, "height": 10}, "device_scale_factor": 1.5}
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


async def md2img(markdown: str, page_option: dict | None = None, extra_screenshot_option: dict | None = None) -> bytes:
    return await html2img(convert_md(markdown), page_option, extra_screenshot_option)


async def template2img(
    template: str | Template | Path,
    params: dict,
    page_option: dict | None = None,
    extra_screenshot_option: dict | None = None
) -> bytes:
    if isinstance(template, str):
        template = Template(template)
    elif isinstance(template, Path):
        if not template.is_file():
            raise ValueError("Path for template is not a file!") 
        template = Template(template.read_text(encoding="utf-8"))
    return await html2img(template.render(params), page_option, extra_screenshot_option)
