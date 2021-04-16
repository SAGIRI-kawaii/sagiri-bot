from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, Integer, String, DateTime, Boolean, BLOB

from .ORM import orm

session = sessionmaker(orm.engine)

Base = orm.Base


class ChatRecord(Base):
    """ 聊天记录表 """
    __tablename__ = "chat_record"

    id = Column(Integer, primary_key=True)
    time = Column(DateTime, nullable=False)
    group_id = Column(Integer, nullable=False)
    member_id = Column(Integer, nullable=False)
    content = Column(String(length=4000), nullable=False)
    seg = Column(String(length=4000), nullable=False)


class BlackList(Base):
    """ 黑名单表 """
    __tablename__ = "black_list"

    member_id = Column(Integer, primary_key=True)


class UserPermission(Base):
    """ 用户等级表（管理权限） """
    __tablename__ = "user_permission"

    group_id = Column(Integer, primary_key=True)
    member_id = Column(Integer, primary_key=True)
    level = Column(Integer, default=1)


class ChatSession(Base):
    """ 用于分配腾讯AI开放平台智能聊天功能session """
    __tablename__ = "chat_session"

    group_id = Column(Integer, primary_key=True)
    member_id = Column(Integer, primary_key=True)
    member_session = Column(Integer, nullable=False)


class Setting(Base):
    """ 群组设置 """
    __tablename__ = "setting"

    group_id = Column(Integer, primary_key=True)
    group_name = Column(String(length=60), nullable=False)
    repeat = Column(Boolean, default=True)
    frequency_limit = Column(Boolean, default=True)
    setu = Column(Boolean, default=False)
    real = Column(Boolean, default=False)
    real_high_quality = Column(Boolean, default=False)
    bizhi = Column(Boolean, default=False)
    r18 = Column(Boolean, default=False)
    img_search = Column(Boolean, default=False)
    bangumi_search = Column(Boolean, default=False)
    compile = Column(Boolean, default=False)
    anti_revoke = Column(Boolean, default=False)
    online_notice = Column(Boolean, default=False)
    debug = Column(Boolean, default=False)
    switch = Column(Boolean, default=True)
    active = Column(Boolean, default=True)
    music = Column(String(length=10), default="off")
    r18_process = Column(String(length=10), default="revoke")
    speak_mode = Column(String(length=10), default="normal")
    long_text_type = Column(String(length=5), default="text")


class UserCalledCount(Base):
    """ 群员调用记录 """
    __tablename__ = "user_called_count"

    group_id = Column(Integer, primary_key=True)
    member_id = Column(Integer, primary_key=True)
    setu = Column(Integer, default=0)
    real = Column(Integer, default=0)
    bizhi = Column(Integer, default=0)
    at = Column(Integer, default=0)
    search = Column(Integer, default=0)
    song_order = Column(Integer, default=0)
    chat_count = Column(Integer, default=0)
    functions = Column(Integer, default=0)


class KeywordReply(Base):
    """ 关键词回复 """
    __tablename__ = "keyword_reply"

    keyword = Column(String(length=200), primary_key=True)
    reply_type = Column(String(length=10), nullable=False)
    reply = Column(BLOB, nullable=False)
    reply_md5 = Column(String(length=32), primary_key=True)


class TriggerKeyword(Base):
    """ 关键词触发功能 """
    __tablename__ = "trigger_keyword"

    keyword = Column(String(length=60), primary_key=True)
    function = Column(String(length=20))


class FunctionCalledRecord(Base):
    """ 功能调用记录 """
    __tablename__ = "function_called_record"

    id = Column(Integer, primary_key=True)
    time = Column(DateTime, nullable=False)
    group_id = Column(Integer, nullable=False)
    member_id = Column(Integer, nullable=False)
    function = Column(String(length=40), nullable=False)
    result = Column(Boolean, default=True)


# class Log(Base):
#     """ 日志 """

# Base.metadata.drop_all(engine)
# Base.metadata.create_all(engine)
