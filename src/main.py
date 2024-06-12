from assistant import Assistant
import time
from dotenv import load_dotenv
load_dotenv()

if __name__ == "__main__":
    assistant = Assistant()
    assistant.start()

    # Keep the main thread running to listen to keyboard events
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Main program interrupted.")
