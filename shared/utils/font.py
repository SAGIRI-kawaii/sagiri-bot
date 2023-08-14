from yarl import URL
from pathlib import Path
from playwright.async_api import Request, Route


font_path = Path.cwd() / "resources" / 'fonts'

font_mime_map = {
    'collection': 'font/collection',
    'otf': 'font/otf',
    'sfnt': 'font/sfnt',
    'ttf': 'font/ttf',
    'woff': 'font/woff',
    'woff2': 'font/woff2',
}


async def fill_font(route: Route, request: Request):
    url = URL(request.url)
    if (font_path / url.name).exists():
        await route.fulfill(
            path=font_path / url.name,
            content_type=font_mime_map.get(url.suffix),
        )
        return
    await route.fallback()
