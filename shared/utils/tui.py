import yaml
from pathlib import Path
from noneprompt import ListPrompt, Choice, InputPrompt

config_path = Path.cwd() / "config1.yaml"
config_demo_path = Path.cwd() / "config_demo.yaml"


def set_config():
    if not config_path.exists():
        with open(config_demo_path, "r", encoding="utf-8") as r:
            content = r.read()
        with open(config_path, "w", encoding="utf-8") as w:
            w.write(content)
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
    print(yaml.dump(configs, encoding='utf-8', allow_unicode=True).decode(encoding="utf-8"))
    with open(config_path, "w", encoding="utf-8") as w:
        w.write(yaml.dump(configs, encoding='utf-8', allow_unicode=True).decode(encoding="utf-8"))
    print("配置已保存")
