from tools.todo_list.add_todo_item_to_list import AddTodoItemToList
from tools.weather.check_weather import CheckWeather
from tools.search.internet_search import InternetSearch
from tools.meal_planning.get_meals_list_tool import GetMealsList
from tools.meal_planning.meal_planning_tool import MealPlanningTool

add_todo_item_to_list = AddTodoItemToList()
check_weather = CheckWeather()
internet_search = InternetSearch()
get_meals_list = GetMealsList()
meal_planning = MealPlanningTool()

tools = {
    add_todo_item_to_list.tool_name: add_todo_item_to_list,
    check_weather.tool_name: check_weather,
    internet_search.tool_name: internet_search,
    get_meals_list.tool_name: get_meals_list,
    meal_planning.tool_name: meal_planning,
}
