from tools.todo_list.add_todo_item_to_list import AddTodoItemToList
from tools.spotify.start_music import StartMusic
from tools.weather.check_weather import CheckWeather

add_todo_item_to_list = AddTodoItemToList()
#start_music = StartMusic()
check_weather = CheckWeather()
tools = {
    add_todo_item_to_list.tool_name: add_todo_item_to_list,
    #start_music.tool_name: start_music
    check_weather.tool_name: check_weather
}