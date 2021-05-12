# from graia.application import GraiaMiraiApplication
# from graia.application.message.chain import MessageChain
# from graia.application.event.messages import Group, Member
#
# from SAGIRIBOT.Handler.Handler import AbstractHandler
#
# from SAGIRIBOT.ORM.AsyncORM import Setting
# from SAGIRIBOT.utils import get_setting, get_admins
#
#
# class HeadHandler(AbstractHandler):
#     """
#     HeadHandler，作为职责链起点
#     """
#     _next_hander = None
#     __name__ = "HeadHandler"
#
#     def set_next(self, handler):
#         self._next_hander = handler
#         return handler
#
#     async def handle(self, app: GraiaMiraiApplication, message: MessageChain, group: Group, member: Member):
#         if not await get_setting(group.id, Setting.switch) and member.id not in await get_admins(group):
#             return None
#         elif self._next_hander:
#             return await self._next_hander.handle(app, message, group, member)
#         return None
