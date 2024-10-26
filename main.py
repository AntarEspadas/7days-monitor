#! usr/bin/env python3

import time
import requests
import os
from requests.sessions import Session
from dotenv import load_dotenv
from collections.abc import Iterable

load_dotenv()


class Monitor:

    def __init__(self, api_url: str, webhook_url: str) -> None:
        self.session = Session()
        self.current_players = set()
        self.api_url = api_url
        self.webhook_url = webhook_url

    def login(self, username: str, password: str):
        json_data = {
            'username': username,
            'password': password,
        }

        self.session.post(f'{self.api_url}/session/login', json=json_data)

    def get_players(self):
        return self.session.get(f'{self.api_url}/api/player').json()

    def _get_formatted_usernames(self, usernames: Iterable[str]):
        return ", ".join(f"**{username}**" for username in usernames)

    def update(self):
        players = self.get_players()
        player_names = set(player["name"] for player in players["data"]["players"])
        disconnected_players = self.current_players.difference(player_names)
        connected_players = player_names.difference(self.current_players)
        if disconnected_players:
            formatted_usernames = self._get_formatted_usernames(disconnected_players)
            message = formatted_usernames + " left the game"
            self.send_webhook(message)
            print(message)
        if connected_players:
            formatted_usernames = self._get_formatted_usernames(connected_players)
            message = formatted_usernames + " joined the game"
            self.send_webhook(message)
            print(message)
        self.current_players = player_names

    def send_webhook(self, content: str):

        json_data = {
            'content': content,
        }

        requests.post(
            self.webhook_url,
            json=json_data,
        )

    def run(self):
        print("Monitoring...")
        while True:
            self.update()
            time.sleep(5)

def get_var(var_name: str) -> str:
    result = os.getenv(var_name)
    if result is None:
        raise Exception("API_URL not set")
    return result

def main():
    api_url = get_var("API_URL")
    webhook_url = get_var("WEBHOOK_URL")
    username = get_var("USERNAME")
    password = get_var("PASSWORD")
    monitor = Monitor(api_url, webhook_url)
    monitor.login(username, password)
    monitor.run()

if __name__ == "__main__":
    main()