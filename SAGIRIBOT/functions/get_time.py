import datetime

from graia.application.message.elements.internal import MessageChain
from graia.application.message.elements.internal import Plain


async def get_postgraduate_entrance_examination_date() -> list:
    now = datetime.datetime.now()
    year, month, day = now.strftime("%Y %m %d").split(" ")
    last_day_this_year = datetime.datetime.strptime(f"{year}-12-31 08:30:00", "%Y-%m-%d %H:%M:%S")
    last_day_weekday_this_year = last_day_this_year.weekday()
    print(last_day_weekday_this_year)
    difference = last_day_weekday_this_year - 6 if last_day_weekday_this_year >= 6 else last_day_weekday_this_year + 2
    postgraduate_entrance_examination_date_this_year = last_day_this_year - datetime.timedelta(days=difference)
    if postgraduate_entrance_examination_date_this_year >= now:
        return [
            postgraduate_entrance_examination_date_this_year.strftime("%Y-%m-%d %H:%M:%S"),
            postgraduate_entrance_examination_date_this_year - now
        ]
    else:
        last_day_next_year = datetime.datetime.strptime(f"{str(int(year)+1)}-12-31", "%Y-%m-%d")
        last_day_weekday_next_year = last_day_this_year.weekday()
        print(last_day_weekday_next_year)
        difference = last_day_weekday_next_year - 6 if last_day_weekday_next_year >= 6 else last_day_weekday_next_year + 2
        postgraduate_entrance_examination_date_next_year = last_day_next_year - datetime.timedelta(days=difference)
        return [
            postgraduate_entrance_examination_date_next_year.strftime("%Y-%m-%d %H:%M:%S"),
            postgraduate_entrance_examination_date_next_year - now
        ]


async def get_time():
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    data = await get_postgraduate_entrance_examination_date()
    days = data[1].days
    data[1] = data[1].seconds
    m, s = divmod(data[1], 60)
    h, m = divmod(m, 60)
    delta_postgraduate_entrance_examination_date = "%d天%0d时%0d分%0d秒" % (days, h, m, s)
    return [
        "quoteSource",
        MessageChain.create([
            Plain(text=f"现在是{now}\n\n"),
            Plain(text=f"考研时间为{data[0].split(' ')[0]}\n\n"),
            Plain(text=f"距今还有{delta_postgraduate_entrance_examination_date}\n\n"),
            Plain(text="加油啊！卷人！你是最卷的！")
        ])
    ]
