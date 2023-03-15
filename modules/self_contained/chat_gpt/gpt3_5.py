import aiohttp

url = "https://api.openai.com/v1/chat/completions"


class GPT35(object):

    def __init__(self, openai_key: str, preset: str, proxy: str = ""):
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
        self.proxy = proxy

    async def send(self) -> dict:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=self.headers, json=self.message, proxy=self.proxy) as resp:
                return await resp.json()

    async def send_message(self, message: str, with_token: bool = True) -> str:
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
        return result["content"] + f"\n\ntoken: {token_used}/4096" if with_token else ""

    def reset(self, preset: str = ""):
        self.message["messages"] = [{"role": "system", "content": preset}] if preset else [self.message["messages"][0]]
