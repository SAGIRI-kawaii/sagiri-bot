from typing import List
from pydantic import BaseModel

from shared.utils.UI.models import ColumnListItemIcon


class IOSColumnListItemIcon(BaseModel):
    awesome_font_name: str = ""
    background_color: str = "blue"
    icon_color: str = "white"
    style: str = ""
    el_name: str = "IOSColumnListItemIcon"


class IOSColumnListItem(BaseModel):
    subtitle: str = ""
    content: str = ""
    left_element: IOSColumnListItemIcon | None = None
    right_element: ColumnListItemIcon | None = None
    style: str = ""
    el_name: str = "IOSColumnListItem"


class IOSColumnList(BaseModel):
    rows: List[IOSColumnListItem]
    style: str = ""
    el_name: str = "IOSColumnList"
