from datetime import date

from openmeteo_sdk import WeatherApiResponse
from logger import logger, ErrorMessage
from ..tool import Tool
from ..tool_parameter import ToolParameter
import openmeteo_requests
import pandas as pd
from geopy.geocoders import Nominatim

class CheckWeather(Tool):

	def __init__(self):
		self.openmeteo = openmeteo_requests.Client()

	@property
	def tool_name(self) -> str:
		return "check_weather"

	@property
	def description(self) -> str:
		return "Check the weather in a specific city at a specific date."

	@property
	def parameters(self) -> list[ToolParameter]:
		return [
			ToolParameter("city", "The name of the city. If user did not specify a city, it will default to Lyon", "string", required=True),
			ToolParameter("date", f"The date - format YYYY-MM-DD. Today we are {date.today().strftime('%Y-%m-%d')}", "string", required=True),
		]

	def _get_coordinates(self, city_name):
		geolocator = Nominatim(user_agent="geoapi")
		location = geolocator.geocode(city_name)
		if location:
			return location.latitude, location.longitude
		else:
			return None

	def _call_api(self, latitude: float, longitude: float, date: str) -> WeatherApiResponse:
		url = "https://api.open-meteo.com/v1/forecast"
		params = {
			"latitude": latitude,
			"longitude": longitude,
			"hourly": ["temperature_2m", "precipitation_probability", "precipitation", "wind_speed_10m"],
			"start_date": date,
			"end_date": date
		}
		responses = self.openmeteo.weather_api(url, params=params)
		return responses[0]

	def _format_answer_to_df(self, openmeteo_response: WeatherApiResponse):
		hourly = openmeteo_response.Hourly()
		hourly_temperature_2m = hourly.Variables(0).ValuesAsNumpy()
		hourly_precipitation_probability = hourly.Variables(1).ValuesAsNumpy()
		hourly_precipitation = hourly.Variables(2).ValuesAsNumpy()
		hourly_wind_speed_10m = hourly.Variables(3).ValuesAsNumpy()

		hourly_data = {"date": pd.date_range(
			start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
			end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
			freq=pd.Timedelta(seconds=hourly.Interval()),
			inclusive="left"
		)}
		hourly_data["temperature_2m"] = hourly_temperature_2m
		hourly_data["precipitation_probability"] = hourly_precipitation_probability
		hourly_data["precipitation"] = hourly_precipitation
		hourly_data["wind_speed_10m"] = hourly_wind_speed_10m
		# print(hourly_data)
		hourly_dataframe = pd.DataFrame(data=hourly_data)
		hourly_dataframe.set_index("date", inplace=True)

		return hourly_dataframe

	def execute(self, city: str, date: str):
		try:
			latitude, longitude = self._get_coordinates(city)
			response = self._call_api(latitude, longitude, date)
			hourly_dataframe = self._format_answer_to_df(response)

			return (f"Here is a dataframe of the hourly weather in {city} on {date}:\n"
					f"Here are some definitions:"
					f"- temperature_2m: Air temperature at 2 meters above ground in °C"
					f"- precipitation_probability: Probability of precipitation in %"
					f"- precipitation: Precipitation in mm"
					f"- wind_speed_10m: Wind speed at 10 meters above ground in km/h\n"
					f"{hourly_dataframe.to_csv()}"
					f"If the user asked for the weather on its daily cycle ride to go to work, focus on the hours: 8 to 9am and 7 to 8pm ONLY"
					)
		except Exception as e:
			logger.log(ErrorMessage(content=f"{self.__class__.__name__} : check_weather: {e}"))
			raise Exception(f"{self.__class__.__name__} : check_weather: {e}")
