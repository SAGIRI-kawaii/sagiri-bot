from typing import Union

from graia.application.message.chain import MessageChain

from SAGIRIBOT.MessageSender.Strategy import Strategy


class MessageItem:
    message: MessageChain
    strategy: Strategy

    def __init__(self, message: Union[MessageChain, None], strategy: Strategy):
        self.message = message
        self.strategy = strategy
