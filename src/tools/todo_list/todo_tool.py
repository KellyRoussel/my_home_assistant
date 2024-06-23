import time
from abc import ABC
import json

import requests
from requests_oauthlib import OAuth2Session
import os

from .entities.todo_list import TodoList
from ..tool import Tool

os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'  # https://github.com/VannTen/oauth2token/issues/5


class TodoTool(Tool, ABC):
    token_file = './src/tools/todo_list/secret_token.json'

    def __init__(self):
        try:
            self.tenant_id = os.environ["MICROSOFT_TENANT_ID"]
            self.client_id = os.environ["MICROSOFT_CLIENT_ID"]
            self.client_secret = os.environ["MICROSOFT_CLIENT_SECRET"]
            self.token = json.load(open(self.token_file))
        except Exception as e:
            raise Exception(f"TodoTool: {e}")

    def _get_access_token(self):
        try:
            now = time.time()
            expire_time = self.token['expires_at'] - 300
            if now >= expire_time:
                self.__refresh_token()

            return self.token['access_token']
        except Exception as e:
            raise Exception(f"_get_access_token: {e}")

    def __refresh_token(self) -> None:
        try:
            oa_sess = OAuth2Session(self.client_id, scope='openid offline_access Tasks.ReadWrite',
                                    token=self.token, redirect_uri='https://localhost/login/authorized')

            self.token = oa_sess.refresh_token('https://login.microsoftonline.com/common/oauth2/v2.0/token',
                                               client_id=self.client_id, client_secret=self.client_secret)
            json.dump(self.token, open(self.token_file, 'w'))
        except Exception as e:
            raise Exception(f"__refresh_token: {e}")

    def _get_todo_list_from_name(self, name):
        try:
            token = self._get_access_token()
            graph_url = 'https://graph.microsoft.com/v1.0/me/todo/lists'

            headers = {
                'Authorization': f'Bearer {token}'
            }

            response = requests.get(graph_url, headers=headers)
            response.raise_for_status()

            todo_lists = response.json()['value']

            todo_list = next((item for item in todo_lists if item['displayName'] == name), None)

            if todo_list is None:
                raise Exception(f"Could not find list with name: {name}")

            return TodoList.from_json(todo_list)
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} : _get_todo_list_from_name: {e}")