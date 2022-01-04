from typing import Union

from graia.ariadne.message.chain import MessageChain

from sagiri_bot.message_sender.strategy import Strategy


class MessageItem(object):
    message: MessageChain
    strategy: Strategy

    def __init__(self, message: Union[MessageChain, None], strategy: Strategy):
        self.message = message
        self.strategy = strategy
