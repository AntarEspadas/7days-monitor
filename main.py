#! usr/bin/env python3

import os
import re
import json
import asyncio
import aiohttp
from dotenv import load_dotenv
from collections.abc import Iterable

from aiosseclient import aiosseclient

load_dotenv()


class Monitor:

    def __init__(self, api_url: str, webhook_url: str) -> None:
        self.current_players = set()
        self.api_url = api_url
        self.webhook_url = webhook_url

    async def __aenter__(self):
        self.session = await aiohttp.ClientSession().__aenter__()
        return self

    async def __aexit__(self, exec_type, exec_val, exec_tb):
        await self.session.__aexit__(exec_type, exec_val, exec_tb)

    async def login(self, username: str, password: str):
        json_data = {
            'username': username,
            'password': password,
        }

        await self.session.post(f'{self.api_url}/session/login', json=json_data)

    async def get_players(self):
        response = await self.session.get(f'{self.api_url}/api/player')
        return await response.json()

    def _get_formatted_usernames(self, usernames: Iterable[str]):
        return ", ".join(f"**{username}**" for username in usernames)

    async def send_webhook(self, content: str):

        json_data = {
            'content': content,
        }

        await self.session.post(
            self.webhook_url,
            json=json_data,
        )

    async def run(self):
        print("Monitoring...")
        sid = None
        for payload in self.session.cookie_jar:
            if payload.key == "sid":
                sid = payload.value
                break
        
        if sid is None:
            raise Exception(f"Could not retrieve session ID")

        headers = {
            "cookie": f"sid={sid}"
        }

        async for payload in aiosseclient(f"{self.api_url}/sse/?events=log", headers=headers):
            if payload.data == "":
                continue
            data: dict = json.loads(payload.data)
            msg = data.get("msg", None)
            if msg is None:
                continue
            matches = re.match(".*Player '(.*)' joined the game.*", msg)
            if matches is not None:
                username = matches.groups()[0]
                message = f"**{username}** joined the game"
                print(message)
                await self.send_webhook(message)
                continue
            matches = re.match(".*Player '(.*)' left the game.*", msg)
            if matches is not None:
                username = matches.groups()[0]
                message = f"**{username}** left the game"
                print(message)
                await self.send_webhook(message)
                continue


def get_var(var_name: str) -> str:
    result = os.getenv(var_name)
    if result is None:
        raise Exception("API_URL not set")
    return result

async def main():
    api_url = get_var("API_URL")
    webhook_url = get_var("WEBHOOK_URL")
    username = get_var("USERNAME")
    password = get_var("PASSWORD")

    async with Monitor(api_url, webhook_url) as monitor:
        await monitor.login(username, password)
        await monitor.run()


if __name__ == "__main__":
    asyncio.run(main())