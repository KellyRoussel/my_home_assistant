import keyboard
from keyboard._keyboard_event import KEY_DOWN, KEY_UP, KeyboardEvent

class KeyboardActionListener:

    def __init__(self):
        try:
            self._press_callback = None
            self._release_callback = None
            self._is_space_pressed = False
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} : __init__: {e}")

    def _on_action(self, event: KeyboardEvent):
        if event.event_type == KEY_DOWN:
            self._on_press(event)

        elif event.event_type == KEY_UP:
            self._on_release(event)

    def _on_press(self, event: KeyboardEvent):
        try:
            if event.name == 'space' and self._press_callback and not self._is_space_pressed:
                self._is_space_pressed = True
                self._press_callback()
        except Exception as e:
            raise Exception(f"on_press: {e}")

    def _on_release(self, event: KeyboardEvent):
        try:
            if event.name == 'space' and self._release_callback:
                self._is_space_pressed = False
                self._release_callback()
        except Exception as e:
            raise Exception(f"on_release: {e}")

    def start_listening(self):
        try:
            keyboard.hook(lambda e: self._on_action(e))
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} : start_listening: {e}")

    def set_press_callback(self, callback):
        try:
            self._press_callback = callback
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} : set_press_callback: {e}")

    def set_release_callback(self, callback):
        try:
            self._release_callback = callback
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} : set_release_callback: {e}")
