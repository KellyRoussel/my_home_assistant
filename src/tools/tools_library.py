from tools.todo_list.add_todo_item_to_list import AddTodoItemToList
from tools.weather.check_weather import CheckWeather

add_todo_item_to_list = AddTodoItemToList()
check_weather = CheckWeather()

tools = {
    add_todo_item_to_list.tool_name: add_todo_item_to_list,
    check_weather.tool_name: check_weather,
}
