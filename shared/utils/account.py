from kayaku import create

from shared.models.config import GlobalConfig

land_dict = {
    "qq": ["mirai_api_http"]
}


def get_host(land: str) -> list[str | int]:
    res = []
    if land in land_dict:
        config = create(GlobalConfig)
        for protocol in land_dict[land]:
            p_config = getattr(config, protocol)
            res.append(str(p_config.host))
    return res
