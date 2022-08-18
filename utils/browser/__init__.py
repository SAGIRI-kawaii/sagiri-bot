from loguru import logger
from typing import Optional, AsyncIterator
from contextlib import asynccontextmanager
from playwright.async_api import Page, Browser, async_playwright, Playwright


path_to_extension = "./utils/browser/extension/ad"
user_data_dir = "./utils/browser/data"


_browser: Optional[Browser] = None
_playwright: Optional[Playwright] = None


async def init(**kwargs) -> Browser:
    global _browser
    global _playwright
    if _browser:
        return _browser
    _playwright = await async_playwright().start()
    # _browser = await _playwright.chromium.launch_persistent_context(
    #     user_data_dir,
    #     headless=True,
    #     args=[
    #         f"--disable-extensions-except={path_to_extension}",
    #         f"--load-extension={path_to_extension}",
    #     ]
    # )
    _browser = await launch_browser(**kwargs)
    return _browser


async def get_browser(**kwargs) -> Browser:
    return await init(**kwargs)


async def launch_browser(**kwargs) -> Browser:
    return await _playwright.chromium.launch(**kwargs)


@asynccontextmanager
async def get_new_page(**kwargs) -> AsyncIterator[Page]:
    browser = await get_browser()
    page = await browser.new_page(**kwargs)
    try:
        yield page
    finally:
        await page.close()


async def shutdown_browser():
    await _browser.close()
    await _playwright.stop()


async def install_browser():
    logger.info("正在安装 chromium")
    import sys
    from playwright.__main__ import main

    sys.argv = ["", "install", "chromium"]
    try:
        main()
    except SystemExit:
        pass
