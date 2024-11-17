import asyncio
from evdev import InputDevice, categorize, ecodes, list_devices
from select import select
from logger import logger, AppMessage, ErrorMessage

class BluetoothButtonActionListener:
    def __init__(self, device_name):
        self._press_callback = None
        self._release_callback = None
        self._is_button_pressed = False
        self.device_name = device_name
        self.device = None
        self.listening = True
        self._connect_device()

    def _connect_device(self):
        try:
            devices = [InputDevice(path) for path in list_devices()]
            remote_shuttle = next((d for d in devices if d.name == self.device_name), None)
            if remote_shuttle:
                self.device = InputDevice(remote_shuttle.path)
                print(f"{self.__class__.__name__}: Device connected.")
                logger.log(AppMessage(content=f"{self.__class__.__name__}: Device connected."))
            else:
                print(f"Device {self.device_name} not found.")
        except Exception as e:
            logger.log(ErrorMessage(content=f"{self.__class__.__name__} : _connect_device: {e}"))
            raise Exception(f"{self.__class__.__name__} : _connect_device: {e}")

    def _on_action(self, event):
        if event.type == ecodes.EV_KEY:  # Confirm if '1' is correct for button press events
            if event.value == 1:
                self._on_press(event)
            elif event.value == 0:
                self._on_release(event)

    async def start_listening(self):
        self.listening = True
        while self.listening:
            try:
                if not self.device:
                    self._connect_device()
                if self.device:
                    r, _, _ = select([self.device], [], [], 1)  # 1-second timeout
                    if r:
                        for event in self.device.read():
                            self._on_action(event)
            except OSError as e:
                if e.errno == 19:  # No such device
                    print("Device disconnected")
                    logger.log(AppMessage(content="Device disconnected."))
                    self.device = None
                    await asyncio.sleep(1)  # Retry after 1 second
                else:
                    raise e
            except Exception as e:
                logger.log(ErrorMessage(content=f"{self.__class__.__name__} : start_listening: {e}"))
                raise Exception(f"{self.__class__.__name__} : start_listening: {e}")
            await asyncio.sleep(0.1)  # Prevent tight loop if no device

    def stop_listening(self):
        self.listening = False

    def set_press_callback(self, callback):
        self._press_callback = callback

    def set_release_callback(self, callback):
        self._release_callback = callback

    def _on_press(self, event):
        if self._press_callback and not self._is_button_pressed:
            self._is_button_pressed = True
            self._press_callback()

    def _on_release(self, event):
        if self._release_callback:
            self._is_button_pressed = False
            self._release_callback()
