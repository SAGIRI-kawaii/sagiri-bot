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
github_config = config.functions.get("github", {})
auth = aiohttp.BasicAuth(login=github_config.get("username"), password=github_config.get("token"))


class GithubAPILimitExceeded(Exception):
    """未配置 github token，请求次数过多超出限制"""


async def get_commit_branch(sha: str) -> str | None:
    async with aiohttp.ClientSession(auth=auth) as session:
        async with session.get(
            f"https://api.github.com/repos/SAGIRI-kawaii/SAGIRI-BOT/commits/{sha}/branches-where-head"
        ) as resp:
            data = await resp.json(content_type=resp.content_type)
            if data:
                if isinstance(data, list):
                    return data[0].get("name")
                elif isinstance(data, dict) and data.get("message", "").startswith("API rate limit exceeded for"):
                    raise GithubAPILimitExceeded()


async def get_latest_commit(current_branch: str | None = None) -> dict | None:
    url = "https://api.github.com/repos/SAGIRI-kawaii/SAGIRI-BOT/commits"
    async with aiohttp.ClientSession(auth=auth) as session:
        async with session.get(url, proxy=proxy) as resp:
            res = await resp.json()
    if isinstance(res, list):
        if current_branch:
            for r in res:
                if sha := r.get("sha"):
                    try:
                        if current_branch == await get_commit_branch(sha):
                            return r
                    except GithubAPILimitExceeded:
                        return logger.error(
                            "API rate limit exceeded，请前往配置填写 github token，检查输入是否有误或token是否失效"
                        )
        return res[0]
    else:
        logger.error(res.get("message"))


def get_repo() -> Repo | None:
    git_path = Path.cwd() / ".git"
    return Repo(Path.cwd()) if git_path.exists() and git_path.is_dir() else None


def get_current_commit(repo: Repo | None = None) -> Commit | None:
    if not repo:
        repo = get_repo()
    return next(repo.iter_commits()) if repo else None


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


async def self_upgrade(current_branch: bool = True):
    repo = get_repo()
    if not repo:
        return logger.warning("未检测到 .git 文件夹，只有使用 git 时才检测更新！")
    branch = repo.active_branch
    latest_commit = await get_latest_commit(current_branch=str(branch) if current_branch else None)
    if not latest_commit:
        return
    commit_message = latest_commit.get("commit", {}).get("message", "null").replace("\n", " ")
    latest_sha = latest_commit.get("sha")
    current_commit = get_current_commit()
    current_sha = str(current_commit) if current_commit else None
    if not latest_sha:
        return logger.error("获取远端仓库最新提交时失败！")
    logger.info(f"SAGIRI-BOT Local Repository Latest Commit SHA1: {current_sha}")
    logger.info(f"SAGIRI-BOT Remote Repository Latest Commit SHA1: {latest_sha}")
    if current_sha != latest_sha:
        if current_branch:
            logger.debug(f"检测到更新：{current_sha} -> {latest_sha}，更新内容：{commit_message}")
        else:
            try:
                remote_branch = await get_commit_branch(latest_sha)
            except GithubAPILimitExceeded:
                return logger.error("API rate limit exceeded，请前往配置填写 github token，检查输入是否有误或token是否失效")
            logger.debug(f"检测到分支<{remote_branch}>的更新：{current_sha} -> {latest_sha}，更新内容：{commit_message}")
        if auto_upgrade:
            logger.info("正在更新...")
            origin = repo.remotes.origin
            origin.pull()
            logger.success("更新完成，请重启机器人！")
        else:
            await new_commit_notice(latest_sha, current_sha, commit_message)
