from graia.application.message.chain import MessageChain
from SAGIRIBOT.MessageSender.Strategy import Strategy


class MessageItem:
    message: MessageChain
    strategy: Strategy

    def __init__(self, message: MessageChain, strategy: Strategy):
        self.message = message
        self.strategy = strategy
