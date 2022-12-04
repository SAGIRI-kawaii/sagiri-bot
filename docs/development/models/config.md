# 配置模型类

> ## GlobalConfig

Bot全局配置信息（`config.yaml`）

### 模型类定义

```python
class GlobalConfig(BaseModel):
    bot_accounts: list[int]
    default_account: int | None
    host_qq: int
    mirai_host: str = "http://localhost:8080"
    verify_key: str = "1234567890"
    db_link: str = "sqlite+aiosqlite:///data.db"
    web_manager_api: bool = False
    web_manager_auto_boot: bool = False
    gallery: dict = {}
    proxy: str = "proxy"
    auto_upgrade: bool = False
    commands: dict[str, PluginConfig]
    functions: dict = {
        "tencent": {"secret_id": "secret_id", "secret_key": "secret_key"},
        "saucenao_api_key": "saucenao_api_key",
        "lolicon_api_key": "lolicon_api_key",
        "wolfram_alpha_key": "wolfram_alpha_key",
        "github": {"username": "username", "token": "token"},
        "stable_diffusion_api": "stable_diffusion_api"
    }
    log_related: dict = {"error_retention": 14, "common_retention": 7}
    data_related: dict = {
        "lolicon_image_cache": True,
        "network_data_cache": False,
        "automatic_update": False,
        "data_retention": False,
    }
```

具体各项信息可查看 [config.yaml](/configuration/#configyaml)

### 获取 GlobalConfig

GlobalConfig 使用了 creart，所以你可以在任何一个文件获取一个唯一的 GlobalConfig 实例：

```python
from creart import create

from shared.models.config import GlobalConfig


config = create(GlobalConfig)
```

> ## PluginMeta

### 模型类定义

```python
class PluginMeta(BaseModel):
    name: str = ""
    version: str = "0.1"
    display_name: str = ""
    authors: list[str] = []
    description: str = ""
    usage: list[str] = []
    example: list[str] = []
    icon: str = ""
    prefix: list[str] = []
    triggers: list[str] = []
    metadata: dict[str, Any] = {}
```

具体各项信息可查看 [metadata.json](/configuration/#metadatajson)

### 获取 PluginMeta

对于 PluginMeta，有两种获取方式，一种是从路径获取，这种方式多用于在插件中获取当前插件文件夹下的 `metadata.json`：

```python
from shared.models.config import load_plugin_meta


meta = load_plugin_meta(__file__)
```

另外一种是从 `module` 获取（`module` 一般为 `modules.self_conntained.plugin_name` 的形式），这种方式多用于在 `Saya` 中获取已加载插件对应的 `metadata.json`：

```python
from creart import create
from graia.saya import Saya

from shared.models.config import load_plugin_meta_by_module


modules = create(Saya).channels
metas = [load_plugin_meta_by_module(module) for module in modules.keys()]
```
