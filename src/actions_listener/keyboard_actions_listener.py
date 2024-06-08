from pynput import keyboard

class KeyboardActionListener:

    def __init__(self):
        try:
            self._listener = keyboard.Listener(on_press=self._on_press, on_release=self._on_release)
            self._press_callback = None
            self._release_callback = None
            self._is_space_pressed = False
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} : __init__: {e}")

    def _on_press(self, key):
        try:
            if key == keyboard.Key.space and self._press_callback and not self._is_space_pressed:
                self._is_space_pressed = True
                self._press_callback()

        except Exception as e:
            raise Exception(f"on_press: {e}")

    def _on_release(self, key):
        try:
            if key == keyboard.Key.space and self._release_callback:
                self._is_space_pressed = False
                self._release_callback()
        except Exception as e:
            raise Exception (f"on_release: {e}")

    def start_listening(self):
        try:
            self._listener.start()
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
