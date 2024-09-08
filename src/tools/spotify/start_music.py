import os

from .spotify_tool import SpotifyTool
from ..tool_parameter import ToolParameter


class StartMusic(SpotifyTool):

    @property
    def tool_name(self) -> str:
        return "start_music"

    @property
    def description(self) -> str:
        return "Launch music"

    @property
    def parameters(self) -> list[ToolParameter]:
        return []

    def execute(self):
        try:
            self.sp.shuffle(True, device_id=self.current_device['id'])
            self.sp.start_playback(device_id=self.current_device['id'], context_uri=os.environ["SPOTIFY_PREFERRED_PLAYLIST_URI"])  # start playlist
            return "Music started"
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} : get_todo_list_items: {e}")
