from .Artifact import artifact_obtain, ARTIFACT_LIST, Artifact, calculate_strengthen_points
from ..config import STAMINA_RESTORE, MAX_STAMINA
from .json_rw import init_user_info, updata_uid_stamina, user_info, save_user_info

from hoshino import Service

import random

sv = Service("原神圣遗物收集")


@sv.on_fullmatch(["原神副本", "圣遗物副本", "查看原神副本", "查看圣遗物副本"])
async def get_obtain(bot, ev):
    mes = "当前副本如下\n"
    for name in artifact_obtain.keys():
        suits = " ".join(artifact_obtain[name])
        mes += f"{name}  掉落  {suits}\n"
    await bot.send(ev, mes, at_sender=True)


@sv.on_prefix("刷副本")
async def _get_artifact(bot, ev):
    obtain = ev.message.extract_plain_text().strip()
    uid = str(ev['user_id'])
    init_user_info(uid)

    if obtain == "":
        return

    if not (obtain in artifact_obtain.keys()):
        mes = f"没有副本名叫 {obtain} ,发送 原神副本 可查看所有副本"
        await bot.send(ev, mes, at_sender=True)
        return

    if user_info[uid]["stamina"] < 20:
        await bot.send(ev, "体力值不足，请等待体力恢复.\n发送 查看体力值 可查看当前体力", at_sender=True)
        return

    user_info[uid]["stamina"] -= 20
    # 随机掉了几个圣遗物
    r = random.randint(1, 3)
    # 随机获得的狗粮点数
    strengthen_points = random.randint(70000, 100000)
    user_info[uid]["strengthen_points"] += strengthen_points

    mes = f"本次刷取副本为 {obtain} \n掉落圣遗物 {r} 个\n获得狗粮点数 {strengthen_points}\n\n"

    for _ in range(r):
        # 随机一个副本掉落的套装名字,然后随机部件的名字
        r_suit_name = random.choice(artifact_obtain[obtain])
        r_artifact_name = random.choice(ARTIFACT_LIST[r_suit_name]["element"])

        artifact = Artifact(r_artifact_name)

        number = int(len(user_info[uid]["warehouse"])) + 1

        # mes += f"当前仓库编号 {number}\n"
        mes += artifact.get_artifact_CQ_code(number)
        mes += "\n"

        user_info[uid]["warehouse"].append(artifact.get_artifact_dict())

    save_user_info()
    await bot.send(ev, mes, at_sender=True)


@sv.on_prefix("查看圣遗物仓库")
async def _get_warehouse(bot, ev):
    page = ev.message.extract_plain_text().strip()
    uid = str(ev['user_id'])
    init_user_info(uid)
    if page == "":
        page = "1"

    if not page.isdigit():
        await bot.send(ev, "你需要输入一个数字", at_sender=True)
        return

    page = int(page)

    mes = "仓库如下\n"
    txt = ""

    for i in range(5):
        try:
            ar = user_info[uid]["warehouse"][i + (page - 1) * 5]
            artifact = Artifact(ar)
            number = i + (page - 1) * 5 + 1
            # txt += f"\n\n仓库圣遗物编号 {i+(page-1)*5+1}"
            txt += artifact.get_artifact_CQ_code(number)

        except IndexError:
            pass

    if txt == "":
        txt = "当前页数没有圣遗物"

    mes += txt
    mes += f"\n\n当前为仓库第 {page} 页，你的仓库共有 {(len(user_info[uid]['warehouse']) // 5) + 1} 页"

    await bot.send(ev, mes, at_sender=True)


@sv.on_prefix("强化圣遗物")
async def strengthen(bot, ev):
    uid = str(ev['user_id'])
    init_user_info(uid)

    try:
        txt = ev.message.extract_plain_text().replace(" ", "")
        strengthen_level, number = txt.split("级")

    except Exception:
        await bot.send(ev, "指令格式错误", at_sender=True)
        return

    try:
        artifact = user_info[uid]["warehouse"][int(number) - 1]
    except IndexError:
        await bot.send(ev, "圣遗物编号错误", at_sender=True)
        return

    strengthen_level = int(strengthen_level)
    artifact = Artifact(artifact)
    strengthen_point = calculate_strengthen_points(artifact.level + 1, artifact.level + strengthen_level)

    if strengthen_point > user_info[uid]["strengthen_points"]:
        await bot.send(ev,
                       "狗粮点数不足\n你可以发送 刷副本 副本名称 获取狗粮点数\n或者发送 转换狗粮 圣遗物编号 销毁仓库里不需要的圣遗物获取狗粮点数\n发送 转换全部0级圣遗物 可将全部0级圣遗物销毁",
                       at_sender=True)
        return

    user_info[uid]["strengthen_points"] -= strengthen_point

    for _ in range(strengthen_level):
        artifact.strengthen()

    mes = "强化成功，当前圣遗物属性为：\n"
    mes += artifact.get_artifact_detail()

    user_info[uid]["warehouse"][int(number) - 1] = artifact.get_artifact_dict()
    save_user_info()
    await bot.send(ev, mes, at_sender=True)


@sv.on_prefix("圣遗物详情")
async def strengthen(bot, ev):
    number = ev.message.extract_plain_text().strip()
    uid = str(ev['user_id'])
    init_user_info(uid)

    try:
        artifact = user_info[uid]["warehouse"][int(number) - 1]
    except IndexError:
        await bot.send(ev, "编号错误", at_sender=True)
        return

    artifact = Artifact(artifact)
    await bot.send(ev, artifact.get_artifact_detail(), at_sender=True)


@sv.on_prefix("圣遗物洗点")
async def strengthen(bot, ev):
    number = ev.message.extract_plain_text().strip()
    uid = str(ev['user_id'])
    init_user_info(uid)

    try:
        artifact = user_info[uid]["warehouse"][int(number) - 1]
    except IndexError:
        await bot.send(ev, "编号错误", at_sender=True)
        return

    artifact = Artifact(artifact)

    if artifact.level < 20:
        await bot.send(ev, "没有强化满的圣遗物不能洗点", at_sender=True)
        return

    strengthen_points = calculate_strengthen_points(1, artifact.level)
    strengthen_points = int(strengthen_points * 0.5)

    artifact.re_init()
    user_info[uid]["warehouse"][int(number) - 1] = artifact.get_artifact_dict()

    user_info[uid]["strengthen_points"] += strengthen_points

    mes = f"洗点完成，获得返还狗粮 {strengthen_points} \n当前圣遗物属性如下：\n"
    mes += artifact.get_artifact_detail()
    save_user_info()

    await bot.send(ev, mes, at_sender=True)


@sv.on_prefix(["转换狗粮", "转化狗粮"])
async def _transform_strengthen(bot, ev):
    number = ev.message.extract_plain_text().strip()
    uid = str(ev['user_id'])
    init_user_info(uid)

    try:
        artifact = user_info[uid]["warehouse"][int(number) - 1]
    except IndexError:
        await bot.send(ev, "编号错误", at_sender=True)
        return
    artifact = Artifact(artifact)

    strengthen_points = calculate_strengthen_points(0, artifact.level)
    strengthen_points = int(strengthen_points * 0.8)

    del user_info[uid]["warehouse"][int(number) - 1]

    user_info[uid]["strengthen_points"] += strengthen_points

    save_user_info()

    mes = f"转化完成，圣遗物已转化为 {int(strengthen_points)} 狗粮点数\n你当前狗粮点数为 {int(user_info[uid]['strengthen_points'])} "
    await bot.send(ev, mes, at_sender=True)


@sv.on_fullmatch("查看体力值")
async def get_user_stamina(bot, ev):
    uid = str(ev['user_id'])
    init_user_info(uid)
    mes = f"你当前的体力值为 {int(user_info[uid]['stamina'])} ,体力值每 {STAMINA_RESTORE} 分钟恢复1点，自动恢复上限为 {MAX_STAMINA}\n"
    mes += f"你当前的狗粮点数为 {int(user_info[uid]['strengthen_points'])}"
    await bot.send(ev, mes, at_sender=True)


@sv.on_prefix('氪体力')
async def kakin(bot, ev):
    if ev.user_id not in bot.config.SUPERUSERS:
        return
    for m in ev.message:
        if m.type == 'at' and m.data['qq'] != 'all':
            uid = str(m.data['qq'])
            init_user_info(uid)
            user_info[uid]["stamina"] += 60
    save_user_info()
    await bot.send(ev, f"充值完毕！谢谢惠顾～")


@sv.on_fullmatch(["转化全部0级圣遗物", "转换全部0级圣遗物"])
async def _transform_all_strengthen(bot, ev):
    uid = str(ev['user_id'])
    init_user_info(uid)

    _0_level_artifact = 0
    temp_list = []

    for artifact in user_info[uid]["warehouse"]:
        if artifact["level"] == 0:
            _0_level_artifact += 1
        else:
            temp_list.append(artifact)

    strengthen_points = _0_level_artifact * 3024

    user_info[uid]["warehouse"] = temp_list
    user_info[uid]["strengthen_points"] += strengthen_points
    save_user_info()

    await bot.send(ev, f"0级圣遗物已全部转化为狗粮，共转化 {_0_level_artifact} 个圣遗物，获得狗粮点数 {strengthen_points}")


@sv.scheduled_job('interval', minutes=STAMINA_RESTORE)
async def _call():
    updata_uid_stamina()
