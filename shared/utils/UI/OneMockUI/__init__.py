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
        Column(
            elements=[
                ColumnTitle(title="column1"),
                ColumnImage(src="src"),
                ColumnList(
                    rows=[
                        ColumnListItem(subtitle="子标题1", content="内容1", right_element=ColumnListItemSwitch(switch=False)),
                        ColumnListItem(subtitle="子标题2", content="内容2", right_element=ColumnListItemSwitch(switch=True)),
                        ColumnListItem(subtitle="子标题3", content="内容3")
                    ]
                ),
                ColumnUserInfo(
                    name="你好",
                    description="我是纱雾",
                    avatar="url"
                )
            ]
        ),
        Column(
            elements=[
                ColumnTitle(title="column2"),
                ColumnImage(src="src"),
                ColumnList(
                    rows=[
                        ColumnListItem(subtitle="子标题1", content="内容1", right_element=ColumnListItemSwitch(switch=False)),
                        ColumnListItem(subtitle="子标题2", content="内容2", right_element=ColumnListItemSwitch(switch=True)),
                        ColumnListItem(subtitle="子标题3", content="内容3")
                    ]
                ),
                ColumnUserInfo(
                    name="你好",
                    description="我是纱雾",
                    avatar="url"
                )
            ]
        )
    ]
)
image_bytes = await gen(form)
"""
