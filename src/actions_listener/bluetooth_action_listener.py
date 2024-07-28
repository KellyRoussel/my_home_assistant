from evdev import InputDevice, categorize, ecodes, list_devices
from select import select

class BluetoothButtonActionListener:

    def __init__(self, device_path):
        try:
            self._press_callback = None
            self._release_callback = None
            self._is_button_pressed = False
            self.device = InputDevice(device_path)
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} : __init__: {e}")

    def _on_action(self, event):
        if event.type == 1:  # Assuming 115 is the button code for the Bluetooth button
            if event.value == 1:
                self._on_press(event)
            elif event.value == 0:
                self._on_release(event)

    def _on_press(self, event):
        try:
            if self._press_callback and not self._is_button_pressed:
                self._is_button_pressed = True
                self._press_callback()
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} : _on_press: {e}")

    def _on_release(self, event):
        try:
            if self._release_callback:
                self._is_button_pressed = False
                self._release_callback()
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} : _on_release: {e}")

    def start_listening(self):
        try:
            while True:
                r, w, x = select([self.device], [], [])
                for event in self.device.read():
                    self._on_action(event)
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

