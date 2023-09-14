import json

import aiohttp


class GPT:

    def __init__(
        self, 
        openai_key: str, 
        preset: str, 
        proxy: str = "", 
        max_round: int = 10, 
        host: str = "https://api.openai.com/v1/chat/completions"
    ):
        self.message = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "system", "content": preset}
            ]
        }
        self.headers = {
            "ContentType": "application/json",
            "Authorization": f"Bearer {openai_key}"
        }
        self.openai_key = openai_key
        self.proxy = proxy
        self.max_round = max_round
        self.host = host

    async def send(self) -> dict:
        async with aiohttp.ClientSession() as session:
            async with session.post(self.host, headers=self.headers, json=self.message, proxy=self.proxy) as resp:
                return await resp.json()

    async def send_message(self, message: str, custom_message: list = None, with_token: bool = True) -> str:
        if not self.openai_key:
            return "请先配置openai_key！"
        if custom_message:
            self.message["messages"] = custom_message
        self.message["messages"].append(
            {"role": "user", "content": message}
        )
        resp = await self.send()
        if err := resp.get("error"):
            self.message["messages"] = self.message["messages"][:-1]
            return err["message"]
        result = resp["choices"][0]["message"]
        token_used = resp["usage"]["total_tokens"]
        self.message["messages"].append(result)
        self.drop_conversation()
        return result["content"] + (f"\n\ntoken: {token_used}/4096" if with_token else "")

    def drop_conversation(self):
        if len(self.message["messages"]) >= (self.max_round + 1) * 2 + 1:
            new_msg = [self.message["messages"][0]]
            for i in range(3, len(self.message["messages"])):
                new_msg.append(self.message["messages"][i])
            self.message["messages"] = new_msg
            print(json.dumps(self.message, indent=4, ensure_ascii=False))

    def reset(self, preset: str = "", max_round: int = 1000):
        self.message["messages"] = [{"role": "system", "content": preset}] if preset else [self.message["messages"][0]]
        self.max_round = max_round
