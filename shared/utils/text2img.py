import re
from jinja2 import Template
from datetime import datetime

from graiax.text2img.playwright import (
    HTMLRenderer,
    MarkdownConverter,
    PageOption,
    ScreenshotOption,
    convert_text,
)
from graiax.text2img.playwright.renderer import BuiltinCSS

from shared.utils.font import fill_font

footer = (
    '<style>.footer{box-sizing:border-box;position:absolute;left:0;width:100%;background:#eee;'
    'padding:50px 40px;margin-top:50px;font-size:0.85rem;color:#6b6b6b;}'
    '.footer p{margin:5px auto;}</style>'
    f'<div class="footer"><p>由 RedBot 生成</p><p>{datetime.now().strftime("%Y/%m/%d %p %I:%M:%S")}</p></div>'
)

html_render = HTMLRenderer(
    page_option=PageOption(device_scale_factor=1.5),
    screenshot_option=ScreenshotOption(type='jpeg', quality=80, full_page=True, scale='device'),
    css=(
        BuiltinCSS.reset,
        BuiltinCSS.github,
        BuiltinCSS.one_dark,
        BuiltinCSS.container,
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
)

md_converter = MarkdownConverter()


async def text2img(text: str, width: int = 800) -> bytes:
    html = convert_text(text)
    html += footer

    return await html_render.render(
        html,
        extra_page_option=PageOption(viewport={'width': width, 'height': 10}),
    )


async def md2img(text: str, width: int = 800) -> bytes:
    html = md_converter.convert(text)
    html += footer

    return await html_render.render(
        html,
        extra_page_option=PageOption(viewport={'width': width, 'height': 10}),
    )


async def template2img(
    template: str,
    render_option: dict[str, str],
    *,
    extra_page_option: PageOption | None = None,
    extra_screenshot_option: ScreenshotOption | None = None,
) -> bytes:
    """Jinja2 模板转图片
    Args:
        template (str): Jinja2 模板
        render_option (Dict[str, str]): Jinja2.Template.render 的参数
        return_html (bool): 返回生成的 HTML 代码而不是图片生成结果的 bytes
        extra_page_option (PageOption, optional): Playwright 浏览器 new_page 方法的参数
        extra_screenshot_option (ScreenshotOption, optional): Playwright 浏览器页面截图方法的参数
        extra_page_methods (Optional[List[Callable[[Page], Awaitable]]]):
            默认为 None，用于 https://playwright.dev/python/docs/api/class-page 中提到的部分方法，
            如 `page.route(...)` 等
    """
    html_code: str = Template(template).render(**render_option)
    return await html_render.render(
        html_code,
        extra_page_option=extra_page_option,
        extra_screenshot_option=extra_screenshot_option,
    )
