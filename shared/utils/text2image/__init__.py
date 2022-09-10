import jinja2
import markdown
from pathlib import Path

from graia.ariadne import Ariadne
from graiax.playwright import PlaywrightBrowser

from shared.utils.files import read_file

TEMPLATE_PATH = Path(__file__).parent / "template"

env = jinja2.Environment(
    extensions=["jinja2.ext.loopcontrols"],
    loader=jinja2.FileSystemLoader(TEMPLATE_PATH),
    enable_async=True,
)


async def html2image(html: str, wait: int = 0, template_path: str = f"file://{Path.cwd()}", **kwargs) -> bytes:
    browser = Ariadne.current().launch_manager.get_interface(PlaywrightBrowser)
    async with browser.page(**kwargs) as page:
        await page.goto(template_path)
        await page.set_content(html, wait_until="networkidle")
        await page.wait_for_timeout(wait)
        img = await page.screenshot(full_page=True)
    return img


async def md2pic(md: str = None, md_path: str | Path = None, css_path: str = None, width: int = 1920) -> bytes:
    """markdown 转 图片

    Args:
        md (str, optional): markdown 格式文本
        md_path (str, optional): markdown 文件路径
        css_path (str,  optional): css文件路径. Defaults to None.
        width (int, optional): 图片宽度，默认为 500
    Returns:
        bytes: 图片, 可直接发送
    """
    template = env.get_template("markdown.html")
    if not md and not md_path:
        raise ValueError("必须输入 md 或 md_path")
    if not md:
        md = await read_file(md_path)
    md = markdown.markdown(
        md,
        extensions=[
            "pymdownx.tasklist",
            "tables",
            "fenced_code",
            "codehilite",
            "mdx_math",
            "pymdownx.tilde",
        ],
        extension_configs={
            "mdx_math": {"enable_dollar_delimiter": True},
            "codehilite": {"use_pygments": True}
        },
    )

    extra = ""
    if "math/tex" in md:
        katex_css = await read_file(TEMPLATE_PATH / "katex" / "katex.min.b64_fonts.css")
        katex_js = await read_file(TEMPLATE_PATH / "katex" / "katex.min.js")
        mathtex_js = await read_file(TEMPLATE_PATH / "katex" / "mathtex-script-type.min.js")
        extra = (
            f'<style type="text/css">{katex_css}</style>'
            f"<script defer>{katex_js}</script>"
            f"<script defer>{mathtex_js}</script>"
        )

    if css_path:
        css = await read_file(css_path)
    else:
        css = await read_file(TEMPLATE_PATH / "css" / "github-markdown-light.css") + \
              await read_file(TEMPLATE_PATH / "css" / "pygments-default.css")

    return await html2image(
        html=await template.render_async(md=md, css=css, extra=extra),
        viewport={"width": width, "height": 10},
    )
