import aiohttp
from git import Repo, Commit
from pathlib import Path
from loguru import logger

from creart import create
from graia.ariadne import Ariadne
from graia.ariadne.message.chain import MessageChain

from shared.models.config import GlobalConfig

config = create(GlobalConfig)
auto_upgrade = config.auto_upgrade
proxy = config.proxy if config.proxy != "proxy" else ""


async def get_latest_commit() -> dict | None:
    url = "https://api.github.com/repos/SAGIRI-kawaii/SAGIRI-BOT/commits"
    async with aiohttp.ClientSession() as session:
        async with session.get(url, proxy=proxy) as resp:
            res = await resp.json()
    if isinstance(res, list):
        return res[0]
    else:
        logger.error(res.get("message"))


def get_current_commit(repo: Repo | None = None) -> Commit | None:
    if not repo:
        git_path = Path.cwd() / ".git"
        if git_path.exists() and git_path.is_dir():
            repo = Repo(Path.cwd())
        else:
            return None
    return next(repo.iter_commits())


def get_repo() -> Repo | None:
    git_path = Path.cwd() / ".git"
    if git_path.exists() and git_path.is_dir():
        return Repo(Path.cwd())


async def has_new_commit() -> bool:
    latest_sha = (await get_latest_commit()).get("sha")
    current_sha = str(get_current_commit())
    return current_sha and latest_sha and latest_sha != current_sha


async def new_commit_notice(latest_sha: str, current_sha: str, commit_message: str):
    await Ariadne.current().send_friend_message(
        config.host_qq,
        MessageChain(
            f"检测到远端有新的commit：{latest_sha}，当前本地commit：{current_sha}，本次更新内容：{commit_message}，请注意更新"
        )
    )


async def self_upgrade():
    latest_commit = await get_latest_commit()
    latest_sha = latest_commit.get("sha")
    current_commit = get_current_commit()
    current_sha = str(current_commit) if current_commit else None
    if not current_sha:
        return logger.warning("未检测到 .git 文件夹，只有使用 git 时才检测更新！")
    if not latest_sha:
        return logger.error("获取远端仓库最新提交时失败！")
    logger.info(f"SAGIRI-BOT Local Repository Latest Commit SHA1: {current_sha}")
    logger.info(f"SAGIRI-BOT Remote Repository Latest Commit SHA1: {latest_sha}")
    if current_sha != latest_sha:
        logger.debug(f"检测到更新：{current_sha} -> {latest_sha}")
        if auto_upgrade:
            logger.info("正在更新...")
            repo = get_repo()
            if repo.is_dirty():
                return logger.error("检测到本地仓库有不兼容修改，请先执行 commit / stash 或删除变更")
            origin = repo.remotes.origin
            origin.pull()
            logger.success("更新完成，请重启机器人！")
        else:
            await new_commit_notice(latest_sha, current_sha, latest_commit.get("message"))

