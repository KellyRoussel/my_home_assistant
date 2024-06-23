import requests

from tools.todo_list.entities.items import TodoItem


class TodoList:

    def __init__(self, display_name: str, id: str, is_owner: bool, is_shared: bool):
        self._display_name = display_name
        self._id = id
        self._is_owner = is_owner
        self._is_shared = is_shared

    # from json constructor
    @classmethod
    def from_json(cls, json: dict):
        try:
            return cls(
                json['displayName'],
                json['id'],
                json['isOwner'],
                json['isShared']
            )
        except Exception as e:
            raise Exception(f"{cls.__name__} : from_json: {e}")

    @property
    def display_name(self) -> str:
        return self._display_name

    @property
    def id(self) -> str:
        return self._id

    @property
    def is_owner(self) -> bool:
        return self._is_owner

    @property
    def is_shared(self) -> bool:
        return self._is_shared

    @property
    def _url(self) -> str:
        return f'https://graph.microsoft.com/v1.0/me/todo/lists/{self.id}/tasks'

    def __get_headers(self, access_token: str) -> dict:
        return {
            'Authorization': f'Bearer {access_token}'
        }

    def get_items(self, access_token) -> list[TodoItem]:
        """
        Get items from the todo list
        :param access_token: Access token
        :return: List of items
        """
        try:
            response = requests.get(self._url, headers=self.__get_headers(access_token))
            response.raise_for_status()

            items = response.json()['value']
            return [TodoItem.from_json(item) for item in items]

        except Exception as e:
            raise Exception(f"{self.__class__.__name__} : __get_items: {e}")

    def add_item(self, access_token: str, item_name: str) -> None:
        """
        Add an item to the todo list
        :param access_token: Access token
        :param item_name: Name of the item to add
        :return: None
        """
        try:
            payload = {
                'title': item_name
            }

            response = requests.post(self._url, headers=self.__get_headers(access_token), json=payload)
            response.raise_for_status()
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} : __add_item: {e}")
