from pydantic import BaseModel
from typing import List, Literal


class HTMLElement(BaseModel):
    html: str


class ColumnTitle(BaseModel):
    title: str = ""
    style: str = ""
    el_name: str = "ColumnTitle"


class ColumnListItemSwitch(BaseModel):
    switch: bool = False
    style: str = ""
    el_name: str = "ColumnListItemSwitch"


class ColumnListItemCheck(BaseModel):
    checked: bool = False
    style: str = ""
    el_name: str = "ColumnListItemCheck"


class ColumnListItemIcon(BaseModel):
    awesome_font_name: str = ""
    style: str = ""
    el_name: str = "ColumnListItemIcon"


class ColumnListItem(BaseModel):
    subtitle: str = ""
    content: str = ""
    right_element: BaseModel = None
    style: str = ""
    el_name: str = "ColumnListItem"


class ColumnListTextWithItem(BaseModel):
    text: str = ""
    right_element: BaseModel = None
    style: str = ""
    el_name: str = "ColumnListTextWithItem"


class ColumnList(BaseModel):
    rows: List[ColumnListItem]
    style: str = ""
    el_name: str = "ColumnList"


class ColumnUserInfo(BaseModel):
    name: str = ""
    description: str = ""
    avatar: str = ""
    style: str = ""
    el_name: str = "ColumnUserInfo"


class ColumnImage(BaseModel):
    src: str = ""
    style: str = ""
    el_name: str = "ColumnImage"


class Column(BaseModel):
    elements = []


class GenForm(BaseModel):
    columns: List[Column] = []
    color_type: Literal["light", "dark"] = "light"
    load_awesome_font: bool = False
    body_width: int = 580

    def calc_body_width(self):
        different = len(self.columns) - 2
        self.body_width = len(self.columns) * 580 - (different * 20 if different > 0 else 0)
        return self.body_width
