from assistant import Assistant
import time
from dotenv import load_dotenv

from tools.todo_list.add_todo_item_to_list import AddTodoItemToList
from tools.todo_list.get_todo_list import GetTodoListTool

load_dotenv()

if __name__ == "__main__":
    assistant = Assistant()
    #assistant.start()

    # Keep the main thread running to listen to keyboard events
    #try:
    #    while True:
    #        time.sleep(1)
    #except KeyboardInterrupt:
    #    print("Main program interrupted.")

    #tool = AddTodoItemToList()
    #tool.add_item_to_list("courses", "homework")

    tool = GetTodoListTool()
    items = tool.get_todo_list_items("courses")
    for item in items:
        print(item)