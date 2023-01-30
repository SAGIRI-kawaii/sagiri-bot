import yaml
import json
from pathlib import Path
from pydantic import BaseModel
from typing import Literal, Any
from noneprompt import ListPrompt, Choice, InputPrompt, ConfirmPrompt

from shared.utils.type import parse_type

config_path = Path.cwd() / "config.yaml"
config_demo_path = Path.cwd() / "config_demo.yaml"
config_info_path = Path.cwd() / "resources" / "config_exp.json"
config_info_type = Literal["str", "int", "float", "bool", "dict", "list[int]", "list[str]"]


def copy_config_demo():
    if not config_path.exists():
        with open(config_demo_path, "r", encoding="utf-8") as r:
            content = r.read()
        with open(config_path, "w", encoding="utf-8") as w:
            w.write(content)


def set_config():
    copy_config_demo()
    with open(config_path, "r", encoding="utf-8") as r:
        configs = yaml.safe_load(r.read())
    path = []

    def get_current_dict():
        t = configs
        for i in path:
            t = t.get(i)
            if not t:
                raise ValueError(f"Invalid path {'.'.join(path)}")
        return t

    while True:
        _t = get_current_dict()
        res = ListPrompt(
            "请选择你要更改的配置项：",
            choices=[
                Choice(i) for i in get_current_dict().keys()
            ] + [Choice("退出")] + ([Choice("返回上一级")] if path else [])
        ).prompt()
        if res.name == "退出":
            break
        elif res.name == "返回上一级":
            path.pop(-1)
            continue
        path.append(res.name)
        child = _t.get(res.name, "")
        if isinstance(child, dict):
            _t = child
            continue
        value = InputPrompt(f"请输入你要更改的值({type(child)})：", str(child)).prompt()
        _t[res.name] = type(child)(value)
        path.pop(-1)
    content = yaml.dump(configs, encoding='utf-8', allow_unicode=True).decode(encoding="utf-8")
    print(content)
    with open(config_path, "w", encoding="utf-8") as w:
        w.write(content)
    print("配置已保存")


class ConfigInfo(BaseModel):
    name: str
    type: config_info_type
    description: str = ""
    default: Any = None
    children: list["ConfigInfo"] = []
    required: bool = False


validators = {
    "int": lambda x: x.isnumeric(),
    "str": lambda x: True,
    "float": lambda x: parse_type(x, float) is not None,
    "bool": lambda x: parse_type(x, bool) is not None,
    "dict": None,
    "list[int]": None,
    "list[str]": None
}

parse = {
    "int": int,
    "str": str,
    "float": float,
    "bool": bool
}


def process_info(info: ConfigInfo, interact: bool = True) -> int | str | float | bool | list[int] | list[str] | dict | None:
    if info.type in ("int", "str", "float", "bool"):
        if not interact:
            return info.default
        return parse_type(
            InputPrompt(
                f"请输入 {info.name}（{info.description}）",
                validator=validators[info.type],
                default_text=str(info.default) if info.default is not None else None
            ).prompt(), parse[info.type]
        )
    elif info.type in ("list[int]", "list[str]"):
        result = []
        if not interact:
            return result
        child_type = info.type[5:-1]
        while res := InputPrompt(
            f"请输入 {info.name}（{info.description}）（退出此项请直接输入回车）",
            validator=validators[info.type]
        ).prompt():
            result.append(parse_type(res, parse[child_type]))
        return result
    else:
        result = {}
        if interact:
            print(f"{info.name} - {info.description}")
        for i in info.children:
            result[i.name] = process_info(i, interact)
        return result


def config_init():
    if not ConfirmPrompt("未检测到配置文件，是否自动创建并进入初始化？", default_choice=True).prompt():
        exit()
    info_list = [ConfigInfo(**i) for i in json.loads(config_info_path.read_bytes())["configs"]]
    config = {}
    required = ConfirmPrompt("配置文件初始化，是否仅进行启动必要项修改？", default_choice=True).prompt()
    for info in info_list:
        config[info.name] = process_info(info, not (required and not info.required))
    content = yaml.dump(config, encoding='utf-8', allow_unicode=True).decode(encoding="utf-8")
    print(content)
    with open(config_path, "w", encoding="utf-8") as w:
        w.write(content)
    print("配置已保存，即将启动")
