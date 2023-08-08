from yarl import URL
from pathlib import Path
from loguru import logger
from typing import Type, Any

from creart import it
from kayaku import create
from graia.saya import Saya
from launart import Launart
from avilla.core import Avilla
from graia.broadcast import Broadcast
from graia.scheduler import GraiaScheduler
from avilla.elizabeth.protocol import ElizabethProtocol
from avilla.elizabeth.connection.ws_client import ElizabethWsClientConfig, ElizabethWsClientNetworking
from graia.scheduler.saya import GraiaSchedulerBehaviour
from graia.saya.builtins.broadcast import BroadcastBehaviour

from shared.utils.log import set_logger
from shared.utils.modules import load_modules
from shared.models.config import GlobalConfig
from shared.utils.config import initialize_config
from shared.database.service import DatabaseService
from shared.service.launch_time import LaunchTimeService

PROTOCOL_DICT = {
    "mirai_api_http": {
        "protocol": ElizabethProtocol,
        "network": ElizabethWsClientNetworking,
        "config": ElizabethWsClientConfig,
        "types": [URL, str, int],
        "attributes": ["url", "verify_key", "account"]
    }
}
launart = Launart()


def mapl2l(_type: Type, data: list[Any]):
    return _type(data)


def initialize():
    prepare()
    init_avilla()
    init_services()
    init_saya()
    launch_avilla()


def prepare():
    initialize_config()
    set_logger()


def init_saya():
    it(GraiaScheduler)
    saya = it(Saya)
    saya.install_behaviours(
        it(BroadcastBehaviour),
        it(GraiaSchedulerBehaviour)
    )
    load_modules(Path.cwd() / "modules" / "system")
    load_modules(Path.cwd() / "modules" / "common")


def init_services():
    launart.add_component(DatabaseService(create(GlobalConfig).database_setting.db_link))
    launart.add_component(LaunchTimeService())


def init_avilla():
    config = create(GlobalConfig)
    avilla = Avilla(broadcast=it(Broadcast), launch_manager=launart)
    for protocal in config.protocols:
        if not (p := PROTOCOL_DICT.get(protocal)):
            logger.warning(f"当前暂不支持{protocal}协议，自动跳过")
            continue
        logger.info(f"正在初始化协议{protocal}实例")
        count = 0
        if not (info := getattr(config, protocal, None)):
            logger.error(f"未找到{protocal}协议相关配置，自动跳过")
            continue
        protocal_instance = p["protocol"]()
        for account in info.accounts:
            protocol_config = p["config"](*list(map(mapl2l, p["types"], [account.get(i) for i in p["attributes"]])))
            network = p["network"](protocal_instance, protocol_config)
            protocal_instance.service.connections.append(network)
            count += 1
        avilla.apply_protocols(protocal_instance)
        logger.success(f"协议{protocal}成功加载{count}条配置，发生错误{len(info.accounts) - count}条 ({count}/{len(info.accounts)})")


def launch_avilla():
    logger.info("准备启动avilla...")
    launart.launch_blocking()
    logger.info("SAGIRI-BOT 已退出")
