from io import BytesIO
from lxml import etree
import os
from PIL import Image, ImageDraw, ImageFont
import random
from typing import List


# Settings
# Base Directory
baseDir = os.path.dirname(os.path.abspath(__file__))
# Tag
defaultTag = '日系推理'
# Font
fontSize = 16
color = '#363636'
zhPerRow = 20
fontsDir = os.path.join(baseDir, 'fonts')
fontFile = '华康翩翩体W5-A.ttf'
# Image
background = 'white'
imagesDir = os.path.join(baseDir, 'images')
coversDir = os.path.join(imagesDir, 'covers')
enableCache = True


async def getHtmlContent(url: str):
    from fake_useragent import UserAgent
    import aiohttp
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url=url, headers={'User-Agent': UserAgent().random}) as resp:
                return await resp.read() if resp.status == 200 else None
    except Exception as e:
        print(e)


async def getTagUrl(tag: str):
    prefix = 'https://book.douban.com/tag/'
    infix = '?start='
    suffix = '&type=T'
    content = await getHtmlContent(prefix + tag)
    if content:
        root: etree.ElementBase = etree.HTML(content.decode('utf-8'))
        empty: etree.ElementBase = root.xpath('//*[@id="subject_list"]/p')
        if not empty or empty.text != '没有找到符合条件的图书':
            anchor = root.xpath('//*[@id="subject_list"]/div[2]/a[last()]/text()')
            cnt = int(anchor[0]) if anchor else 0
            page = random.randint(0, cnt) if cnt > 0 else 0
            return prefix + tag + infix + str(page * 20) + suffix if tag else None


async def getBookCoverUrlAndIntro(url: str):
    content = await getHtmlContent(url)
    if content:
        root: etree.ElementBase = etree.HTML(content.decode('utf-8'))
        href = root.xpath('//*[@id="mainpic"]/a/@href')
        coverUrl = str(href[0]) if href else None
        infix = 'doubanio.com/view/subject/l/public/'
        if coverUrl and coverUrl.find(infix) != -1:
            paras: List[etree.ElementBase] = root.xpath('//*[@id="link-report"]/div[1]/div/p')
            if not paras:
                paras = root.xpath('//*[@id="link-report"]/span[1]/div/p')
            intro = ''
            for para in paras:
                text = str(para.text)
                if text != 'None':
                    intro += text + '\n'
            intro = intro.strip(' \n')
            return coverUrl, (intro if intro else '(暂无内容简介)')
    return None, None


async def getBookInfo(url: str):
    content = await getHtmlContent(url)
    if content:
        root: etree.ElementBase = etree.HTML(content.decode('utf-8'))
        cnt = len(root.xpath('//*[@id="subject_list"]/ul/li'))
        index = random.randint(1, cnt) if cnt > 1 else 1
        info = '//*[@id="subject_list"]/ul/li[' + str(index) + ']/div[2]'
        anchor = info + '/h2/a'
        href = root.xpath(anchor + '/@href')
        bookHref = str(href[0]) if href else None
        title = root.xpath(anchor + '/@title')
        bookTitle = str(title[0]) if title else None
        pub = root.xpath(info + '/div[1]/text()')
        bookPub = str(pub[0]).strip(' \n') if pub else None
        rating = root.xpath(info + '/div[2]/span[2]/text()')
        bookRating = str(rating[0]).strip(' \n') if rating else None
        if not bookRating:
            rating = root.xpath(info + '/div[2]/div[2]/span/text()')
            bookRating = str(rating[0]).strip(' \n') if rating else None
            if not bookRating:
                bookRating = '(暂无评分)'
        prefix = 'https://book.douban.com/subject/'
        if bookHref and bookHref.startswith(prefix) and bookTitle and bookPub and bookRating:
            bookId = bookHref.split('/')[-2]
            bookCoverUrl, bookIntro = await getBookCoverUrlAndIntro(bookHref)
            if bookId and bookCoverUrl and bookIntro:
                return {'title': bookTitle, 'pub': bookPub, 'rating': bookRating,
                        'id': bookId, 'coverUrl': bookCoverUrl, 'intro': bookIntro}


async def getCoverImage(bookInfo: dict):
    path = os.path.join(coversDir, bookInfo['id'] + '.jpg')
    if enableCache and os.path.isfile(path):
        return Image.open(path)
    content = await getHtmlContent(bookInfo['coverUrl'])
    if content:
        image: Image.Image = Image.open(BytesIO(content))
        if enableCache:
            image.save(path, quality=95, subsampling=0)
        return image


async def getFormatInfo(bookInfo: dict):
    base = '《' + bookInfo['title'] + '》\n\n出版信息：' + bookInfo['pub'] + \
           '\n\n豆瓣评分：' + bookInfo['rating'] + '\n\n内容简介：\n\n' + bookInfo['intro'] + '\n'
    info = ''
    cnt = 0
    for ch in base:
        if len(ch.encode('utf-8')) > 1:
            if cnt + 2 > 2 * zhPerRow:
                info += '\n' + ch
                cnt = 2
            else:
                info += ch
                cnt += 2
        elif ch == '\n':
            info += '\n'
            cnt = 0
        elif cnt == 2 * zhPerRow:
            info += '\n' + ch
            cnt = 1
        else:
            info += ch
            cnt += 1
    return info


async def getImagePath(tag: str = defaultTag):
    tag = tag.strip()
    url = await getTagUrl(tag if tag else defaultTag)
    if url:
        bookInfo = await getBookInfo(url)
        if bookInfo:
            path = os.path.join(imagesDir, bookInfo['id'] + '.jpg')
            if enableCache and os.path.isfile(path):
                return path
            cover = await getCoverImage(bookInfo)
            if cover:
                infoWidth = (zhPerRow + 1) * fontSize
                info = await getFormatInfo(bookInfo)
                cover = cover.resize((infoWidth, cover.size[1] * infoWidth // cover.size[0]), Image.ANTIALIAS)
                image = Image.new('RGB', (infoWidth, cover.size[1] + (info.count('\n') + 2) * fontSize), background)
                image.paste(cover, (0, 0))
                padding = int(fontSize / 2)
                font = ImageFont.truetype(os.path.join(fontsDir, fontFile), fontSize)
                ImageDraw.Draw(image).text((padding, cover.size[1] + padding), info, color, font, spacing=1)
                image.save(path, quality=95, subsampling=0)
                return path
