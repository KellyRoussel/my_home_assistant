from abc import ABC
import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from ..tool import Tool


class SpotifyTool(Tool, ABC):

    def __init__(self):
        try:
            client_id = os.environ["SPOTIFY_CLIENT_ID"]
            client_secret = os.environ["SPOTIFY_CLIENT_SECRET"]
            redirect_uri = os.environ["SPOTIFY_REDIRECT_URI"]
            scope = "user-library-read, user-read-playback-state, user-modify-playback-state"
            self.sp = spotipy.Spotify(
                auth_manager=SpotifyOAuth(scope=scope, client_id=client_id, client_secret=client_secret,
                                          redirect_uri=redirect_uri))

            devices = self.sp.devices()
            self.current_device = devices['devices'][0] # TODO: replace with raspberry client
        except Exception as e:
            raise Exception(f"SpotifyTool: {e}")

