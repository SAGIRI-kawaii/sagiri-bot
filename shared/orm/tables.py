from sqlalchemy import Column, Integer, String, DateTime, Boolean, BIGINT, Text

from . import Base


class ChatRecord(Base):
    """聊天记录表"""

    __tablename__ = "chat_record"

    id = Column(Integer, primary_key=True)
    time = Column(DateTime, nullable=False)
    group_id = Column(BIGINT, nullable=False)
    member_id = Column(BIGINT, nullable=False)
    persistent_string = Column(String(length=4000), nullable=False)
    seg = Column(String(length=4000), nullable=False)


class BlackList(Base):
    """黑名单表"""

    __tablename__ = "black_list"

    member_id = Column(BIGINT, primary_key=True)
    group_id = Column(BIGINT, primary_key=True)


class UserPermission(Base):
    """用户等级表（管理权限）"""

    __tablename__ = "user_permission"

    group_id = Column(BIGINT, primary_key=True)
    member_id = Column(BIGINT, primary_key=True)
    level = Column(Integer, default=1)


class Setting(Base):
    """群组设置"""

    __tablename__ = "setting"

    group_id = Column(BIGINT, primary_key=True)
    group_name = Column(String(length=60), nullable=False)
    frequency_limit = Column(Boolean, default=True)
    r18 = Column(Boolean, default=False)
    r18_process = Column(String(length=15), default="")
    anti_revoke = Column(Boolean, default=False)
    anti_flash_image = Column(Boolean, default=False)
    online_notice = Column(Boolean, default=False)
    daily_newspaper = Column(Boolean, default=False)
    switch = Column(Boolean, default=True)
    active = Column(Boolean, default=True)


class UserCalledCount(Base):
    """群员调用记录"""

    __tablename__ = "user_called_count"

    group_id = Column(BIGINT, primary_key=True)
    member_id = Column(BIGINT, primary_key=True)
    setu = Column(Integer, default=0)
    real = Column(Integer, default=0)
    bizhi = Column(Integer, default=0)
    at = Column(Integer, default=0)
    search = Column(Integer, default=0)
    song_order = Column(Integer, default=0)
    chat_count = Column(Integer, default=0)
    functions = Column(Integer, default=0)


class KeywordReply(Base):
    """关键词回复"""

    __tablename__ = "keyword_reply"

    keyword = Column(String(length=200), primary_key=True)
    group = Column(BIGINT, default=-1)
    reply_type = Column(String(length=10), nullable=False)
    reply = Column(Text, nullable=False)
    reply_md5 = Column(String(length=32), primary_key=True)


class TriggerKeyword(Base):
    """关键词触发功能"""

    __tablename__ = "trigger_keyword"

    keyword = Column(String(length=60), primary_key=True)
    function = Column(String(length=20))


class FunctionCalledRecord(Base):
    """功能调用记录"""

    __tablename__ = "function_called_record"

    id = Column(Integer, primary_key=True)
    time = Column(DateTime, nullable=False)
    group_id = Column(BIGINT, nullable=False)
    member_id = Column(BIGINT, nullable=False)
    function = Column(String(length=40), nullable=False)
    result = Column(Boolean, default=True)


class LoliconData(Base):
    """lolicon api数据"""

    __tablename__ = "lolicon_data"

    pid = Column(BIGINT, primary_key=True)
    p = Column(Integer, primary_key=True)
    uid = Column(BIGINT, nullable=False)
    title = Column(String(length=200), nullable=False)
    author = Column(String(length=200), nullable=False)
    r18 = Column(Boolean, nullable=False)
    width = Column(Integer, nullable=False)
    height = Column(Integer, nullable=False)
    tags = Column(String(length=1000), nullable=False)
    ext = Column(String(length=20), nullable=False)
    upload_date = Column(DateTime, nullable=False)
    original_url = Column(String(length=200), nullable=False)


class GroupTeam(Base):
    """group_team 群小组"""

    __tablename__ = "group_team"

    creator = Column(BIGINT)
    group_id = Column(BIGINT, primary_key=True)
    name = Column(String(length=200), primary_key=True)
    teammates = Column(Text)


class ChatClips(Base):
    """chat_clips 群片段记录"""

    __tablename__ = "chat_clips"

    cid = Column(Integer, primary_key=True)
    group_id = Column(BIGINT)
    member_id = Column(BIGINT)
    uid = Column(BIGINT)


class BilibiliSubscribe(Base):
    """bilibili_subscribe Bilibili订阅"""

    __tablename__ = "bilibili_subscribe"

    group_id = Column(BIGINT, primary_key=True)
    member_id = Column(BIGINT)
    uid = Column(BIGINT, primary_key=True)


class GroupMembersBackup(Base):
    """group_member_backup 群成员备份"""

    __tablename__ = "group_member_backup"

    group_id = Column(BIGINT, primary_key=True)
    group_name = Column(String(length=60), nullable=False)
    members = Column(String(length=4000), nullable=False)


class APIAccount(Base):
    """api_account 管理面板账户"""

    __tablename__ = "api_account"

    applicant = Column(BIGINT)
    username = Column(String(length=60), primary_key=True)
    password = Column(String(length=60))
