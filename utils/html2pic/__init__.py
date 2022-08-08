import os
import jinja2
import aiofiles
import markdown
from pathlib import Path
from loguru import logger
from typing import Optional

from utils.browser import get_new_page

TEMPLATES_PATH = str(Path(__file__).parent / "templates")
BASE_URL = f"file://{os.getcwd()}"
env = jinja2.Environment(
    extensions=["jinja2.ext.loopcontrols"],
    loader=jinja2.FileSystemLoader(TEMPLATES_PATH),
    enable_async=True,
    autoescape=True,
)


async def read_file(path: str) -> str:
    async with aiofiles.open(path, mode="r") as f:
        return await f.read()


async def read_tpl(path: str) -> str:
    return await read_file(f"{TEMPLATES_PATH}/{path}")


async def html_to_pic(
    html: str, wait: int = 0, template_path: str = f"file://{os.getcwd()}", **kwargs
) -> bytes:
    """html转图片
    Args:
        html (str): html文本
        wait (int, optional): 等待时间. Defaults to 0.
        template_path (str, optional): 模板路径 如 "file:///path/to/template/"
    Returns:
        bytes: 图片, 可直接发送
    """
    if "file:" not in template_path:
        raise ValueError("template_path 应该为 file:///path/to/template")
    async with get_new_page(**kwargs) as page:
        await page.goto(template_path)
        await page.set_content(html, wait_until="networkidle")
        await page.wait_for_timeout(wait)
        img_raw = await page.screenshot(full_page=True)
    return img_raw


async def text_to_pic(text: str, css_path: str = None, width: int = 500) -> bytes:
    """多行文本转图片
    Args:
        text (str): 纯文本, 可多行
        css_path (str, optional): css文件
        width (int, optional): 图片宽度，默认为 500
    Returns:
        bytes: 图片, 可直接发送
    """
    template = env.get_template("text.html")

    return await html_to_pic(
        template_path=f"file://{css_path if css_path else TEMPLATES_PATH}",
        html=await template.render_async(
            text=text,
            css=await read_file(css_path) if css_path else await read_tpl("text.css"),
        ),
        viewport={"width": width, "height": 10},
    )


async def template_to_pic(
    template_path: str,
    template_name: str,
    templates: dict,
    pages: dict = {
        "viewport": {"width": 500, "height": 10},
        "base_url": f"file://{os.getcwd()}",
    },
    wait: int = 0,
) -> bytes:
    """使用jinja2模板引擎通过html生成图片
    Args:
        template_path (str): 模板路径
        template_name (str): 模板名
        templates (dict): 模板内参数 如: {"name": "abc"}
        pages (dict): 网页参数 Defaults to {"base_url": f"file://{getcwd()}", "viewport": {"width": 500, "height": 10}}
        wait (int, optional): 网页载入等待时间. Defaults to 0.
    Returns:
        bytes: 图片 可直接发送
    """

    template_env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(template_path),
        enable_async=True,
        autoescape=True,
    )
    template = template_env.get_template(template_name)

    return await html_to_pic(
        template_path=f"file://{template_path}",
        html=await template.render_async(**templates),
        wait=wait,
        **pages,
    )


async def md_to_pic(
    md: str = None, md_path: str = None, css_path: str = None, width: int = 500
) -> bytes:
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
    if not md:
        if md_path:
            md = await read_file(md_path)
        else:
            raise ValueError("必须输入 md 或 md_path")
    logger.debug(md)
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
        extension_configs={"mdx_math": {"enable_dollar_delimiter": True}},
    )

    logger.debug(md)
    extra = ""
    if "math/tex" in md:
        katex_css = await read_tpl("katex/katex.min.b64_fonts.css")
        katex_js = await read_tpl("katex/katex.min.js")
        mathtex_js = await read_tpl("katex/mathtex-script-type.min.js")
        extra = (
            f'<style type="text/css">{katex_css}</style>'
            f"<script defer>{katex_js}</script>"
            f"<script defer>{mathtex_js}</script>"
        )

    if css_path:
        css = await read_file(css_path)
    else:
        css = await read_tpl("github-markdown-light.css") + await read_tpl(
            "pygments-default.css"
        )

    return await html_to_pic(
        template_path=f"file://{css_path if css_path else TEMPLATES_PATH}",
        html=await template.render_async(md=md, css=css, extra=extra),
        viewport={"width": width, "height": 10},
    )


async def capture_element(
    url: str, element: str, timeout: Optional[float] = 0, **kwargs
) -> bytes:
    async with get_new_page(**kwargs) as page:
        await page.goto(url, timeout=timeout)
        img_raw = await page.locator(element).screenshot()
    return img_raw
