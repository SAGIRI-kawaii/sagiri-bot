from pathlib import Path

from shared.utils.UI.models import *
from shared.utils.text2img import template2img


async def gen(form: GenForm) -> bytes:
    template = Path(__file__).parent / "template.html"
    width = form.calc_body_width()
    return await template2img(template, form.dict(), page_option={"viewport": {"width": width, "height": 10}})


# example
"""
form = GenForm(
    columns=[
        Column(elements=[
            ColumnTitle(title="设置"),
            ColumnUserInfo(
                name="UserName",
                description="Apple ID、iCloud、媒体与购买项目",
                avatar="https://gimg2.baidu.com/image_search/src=http%3A%2F%2Fc-ssl.duitang.com%2Fuploads%2Fitem%2F202009%2F23%2F20200923185609_rQUdj.thumb.1000_0.jpeg&refer=http%3A%2F%2Fc-ssl.duitang.com&app=2002&size=f9999,10000&q=a80&n=0&g=0n&fmt=auto?sec=1664606179&t=2733205a7126c9ffb8cb48e37e50eada"
            ),
            ColumnImage(src="https://gimg2.baidu.com/image_search/src=http%3A%2F%2Fimg.jj20.com%2Fup%2Fallimg%2F1113%2F052420110515%2F200524110515-1-1200.jpg&refer=http%3A%2F%2Fimg.jj20.com&app=2002&size=f9999,10000&q=a80&n=0&g=0n&fmt=auto?sec=1664605944&t=d8625700460b2d0b38c83e5e3ab4c783"),
            IOSColumnList(rows=[
                IOSColumnListItem(
                    left_element=IOSColumnListItemIcon(
                        awesome_font_name="fa-plane",
                        background_color="rgb(240, 154, 55)"
                    ),
                    subtitle="飞行模式",
                    right_element=ColumnListItemSwitch(switch=False)
                ),
                IOSColumnListItem(
                    left_element=IOSColumnListItemIcon(
                        awesome_font_name="fa-wifi",
                        background_color="rgb(52, 120, 246)"
                    ),
                    subtitle="无线局域网",
                    right_element=ColumnListTextWithItem(
                        text="未连接",
                        right_element=ColumnListItemIcon(awesome_font_name="fa-chevron-right")
                    )
                ),
                IOSColumnListItem(
                    left_element=IOSColumnListItemIcon(
                        awesome_font_name="fa-bluetooth-b",
                        background_color="rgb(52, 120, 246)"
                    ),
                    subtitle="蓝牙",
                    right_element=ColumnListTextWithItem(
                        text="打开",
                        right_element=ColumnListItemIcon(awesome_font_name="fa-chevron-right")
                    )
                ),
                IOSColumnListItem(
                    left_element=IOSColumnListItemIcon(
                        awesome_font_name="fa-signal",
                        background_color="rgb(101, 196, 102)"
                    ),
                    subtitle="蜂窝网络",
                    right_element=ColumnListItemIcon(awesome_font_name="fa-chevron-right")
                ),
                IOSColumnListItem(
                    left_element=IOSColumnListItemIcon(
                        awesome_font_name="fa-link",
                        background_color="rgb(101, 196, 102)"
                    ),
                    subtitle="个人热点",
                    right_element=ColumnListItemIcon(awesome_font_name="fa-chevron-right")
                ),
                IOSColumnListItem(
                    left_element=IOSColumnListItemIcon(
                        awesome_font_name="fa-wpexplorer",
                        background_color="rgb(52, 120, 246)"
                    ),
                    subtitle="VPN",
                    right_element=ColumnListItemSwitch(switch=True)
                )
            ]),
            IOSColumnList(rows=[
                IOSColumnListItem(
                    left_element=IOSColumnListItemIcon(
                        awesome_font_name="fa-bell",
                        background_color="rgb(235, 77, 61)"
                    ),
                    subtitle="通知",
                    right_element=ColumnListItemSwitch(switch=False)
                ),
                IOSColumnListItem(
                    left_element=IOSColumnListItemIcon(
                        awesome_font_name="fa-volume-up",
                        background_color="rgb(234, 68, 89)"
                    ),
                    subtitle="声音与触感",
                    right_element=ColumnListItemIcon(awesome_font_name="fa-chevron-right")
                ),
                IOSColumnListItem(
                    left_element=IOSColumnListItemIcon(
                        awesome_font_name="fa-moon-o",
                        background_color="rgb(87, 86, 206)"
                    ),
                    subtitle="专注模式",
                    right_element=ColumnListItemIcon(awesome_font_name="fa-chevron-right")
                ),
                IOSColumnListItem(
                    left_element=IOSColumnListItemIcon(
                        awesome_font_name="fa-clock-o",
                        background_color="rgb(52, 120, 246)"
                    ),
                    subtitle="屏幕使用时间",
                    right_element=ColumnListItemIcon(awesome_font_name="fa-chevron-right")
                )
            ]),
        ])
    ],
    color_type="dark"
)
image_bytes = await gen(form)
"""
