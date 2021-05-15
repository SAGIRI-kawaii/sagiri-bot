from tortoise.models import Model
from tortoise.exceptions import DoesNotExist
from tortoise import fields, Tortoise, run_async


class BaseModel(Model):

    @classmethod
    async def execute(cls):
        await cls.execute()

    @classmethod
    async def fetchall(cls):
        return await cls.all()

    @classmethod
    async def fetchone(cls, filter_dict: dict):
        return await cls.all().filter(**filter_dict).first()

    @classmethod
    async def count(cls):
        return await cls.all().count()

    @classmethod
    async def update(cls, filter_dict: dict, data_dict: dict):
        if models := cls.all().filter(**filter_dict):
            return await models.update(**data_dict)
        else:
            return await cls.create(**data_dict)

    @classmethod
    async def add(cls, data_dict: dict):
        return await cls.create(**data_dict)

    @classmethod
    async def remove(cls, filter_dict: dict):
        return await cls.all().filter(**filter_dict).delete()

    class Meta:
        abstract = True


class ChatRecord(BaseModel):
    """ 聊天记录表 """
    id = fields.IntField(pk=True)
    time = fields.DatetimeField(null=False)
    group_id = fields.IntField(null=False)
    member_id = fields.IntField(null=False)
    content = fields.TextField(null=False, max_length=4000)
    seg = fields.TextField(null=False, max_length=4000)

    class Meta:
        name = "chat_record"


class BlackList(BaseModel):
    """ 黑名单表 """
    member_id = fields.IntField(pk=True)

    class Meta:
        name = "black_list"


class UserPermission(BaseModel):
    """ 用户等级表（管理权限） """
    group_id = fields.IntField()
    member_id = fields.IntField()
    level = fields.IntField(default=1)

    class Meta:
        name = "user_permission"
        unique_together = ("group_id", "member_id")


class ChatSession(BaseModel):
    """ 用于分配腾讯AI开放平台智能聊天功能session """
    group_id = fields.IntField()
    member_id = fields.IntField()
    member_session = fields.IntField(null=False)

    class Meta:
        name = "chat_session"
        unique_together = ("group_id", "member_id")


class Setting(BaseModel):
    """ 群组设置 """
    group_id = fields.IntField(pk=True)
    group_name = fields.TextField(null=False, max_length=60)
    repeat = fields.BooleanField(default=True)
    frequency_limit = fields.BooleanField(default=True)
    setu = fields.BooleanField(default=False)
    real = fields.BooleanField(default=False)
    real_high_quality = fields.BooleanField(default=False)
    bizhi = fields.BooleanField(default=False)
    r18 = fields.BooleanField(default=False)
    img_search = fields.BooleanField(default=False)
    bangumi_search = fields.BooleanField(default=False)
    compile = fields.BooleanField(default=False)
    anti_revoke = fields.BooleanField(default=False)
    online_notice = fields.BooleanField(default=False)
    debug = fields.BooleanField(default=False)
    switch = fields.BooleanField(default=True)
    active = fields.BooleanField(default=True)
    music = fields.TextField(default="off", max_length=10)
    r18_process = fields.TextField(default="revoke", max_length=10)
    speak_mode = fields.TextField(default="normal", max_length=10)
    long_text_type = fields.TextField(default="text", max_length=5)

    class Meta:
        name = "setting"


class UserCalledCount(BaseModel):
    """ 群员调用记录 """
    group_id = fields.IntField()
    member_id = fields.IntField()
    setu = fields.IntField(default=0)
    real = fields.IntField(default=0)
    bizhi = fields.IntField(default=0)
    at = fields.IntField(default=0)
    search = fields.IntField(default=0)
    song_order = fields.IntField(default=0)
    chat_count = fields.IntField(default=0)
    functions = fields.IntField(default=0)

    class Meta:
        name = "user_called_count"
        unique_together = ("group_id", "member_id")


class KeywordReply(BaseModel):
    """ 关键词回复 """
    keyword = fields.TextField(max_length=200)
    reply_type = fields.TextField(null=False, max_length=10)
    reply = fields.BinaryField(null=False)
    reply_md5 = fields.TextField(max_length=32)

    class Meta:
        name = "keyword_reply"
        unique_together = ("keyword", "reply_md5")


class TriggerKeyword(BaseModel):
    """ 关键词触发功能 """
    keyword = fields.CharField(pk=True, max_length=60)
    function = fields.TextField(null=False, max_length=20)

    class Meta:
        name = "trigger_keyword"


class FunctionCalledRecord(BaseModel):
    """ 功能调用记录 """
    id = fields.IntField(pk=True)
    time = fields.DatetimeField(null=False)
    group_id = fields.IntField(null=False)
    member_id = fields.IntField(null=False)
    function = fields.TextField(null=False, max_length=40)
    result = fields.BooleanField(default=True)

    class Meta:
        name = "function_called_record"


async def init():
    await Tortoise.init(
        db_url="sqlite://test.db",
        modules={"models": ["SAGIRIBOT.ORM.TortoiseORM"]}
    )
    await Tortoise.generate_schemas()


# run_async(init())
