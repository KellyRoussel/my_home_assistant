from gpiozero import Button
from signal import pause

class ButtonActionListener:

    def __init__(self, pin):
        try:
            self._press_callback = None
            self._release_callback = None
            self._is_button_pressed = False
            self.button = Button(pin)
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} : __init__: {e}")

    def _on_press(self):
        try:
            if self._press_callback and not self._is_button_pressed:
                self._is_button_pressed = True
                self._press_callback()
        except Exception as e:
            raise Exception(f"_on_press: {e}")

    def _on_release(self):
        try:
            if self._release_callback:
                self._is_button_pressed = False
                self._release_callback()
        except Exception as e:
            raise Exception(f"_on_release: {e}")

    def start_listening(self):
        try:
            self.button.when_pressed = self._on_press
            self.button.when_released = self._on_release
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
