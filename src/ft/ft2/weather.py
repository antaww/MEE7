import os
from datetime import datetime

import requests
from dotenv import load_dotenv

load_dotenv()
WEATHER_API_KEY = os.getenv('OPENWEATHER_API_KEY')


def get_weather(city, date):
    """
    Fetches the weather forecast for a specified city and date using the OpenWeatherMap API.

    The function first checks if the provided date is within the acceptable range for the API
    (not in the past and within the next 6 days). It then constructs a request to the API
    to retrieve the weather forecast for the specified city. If the request is successful,
    it searches the forecast data for the weather conditions on the target date and returns
    a dictionary containing the date, city, weather description, and temperature. If the
    target date's weather information is not available or if the request fails, appropriate
    error messages are returned.

    Parameters:
    - city (str): The name of the city for which the weather forecast is requested.
    - date (str): The target date for the weather forecast in 'YYYY-MM-DD' format.

    Returns:
    - dict: A dictionary containing the weather forecast information for the target date
            including the date, city, weather description, and temperature if successful.
    - str: An error message if the date is not within the valid range, if the request fails,
           or if no weather information is available for the provided date.
    """
    # Format the target date string to a datetime object
    target_date = datetime.strptime(date, '%Y-%m-%d')
    today = datetime.now()

    # Calculate the difference in days between the target date and today
    delta_days = (target_date - today).days

    if delta_days < -1:
        return "The date provided is in the past. Please provide a future date."

    # OpenWeatherMap API only provides forecasts for the next 5 days
    if delta_days > 6:
        return "The date provided is too far in the future. Please provide a date within the next 6 days."

    # Construct the API URL for the weather forecast
    url = f"https://api.openweathermap.org/data/2.5/forecast?q={city}&units=metric&appid={WEATHER_API_KEY}"

    # Make a request to the API
    response = requests.get(url)
    data = response.json()

    if response.status_code != 200:
        return f"Error: {data.get('message', 'Impossible to retrieve data.')}"

    # Search for the weather forecast on the target date
    for forecast in data['list']:
        forecast_date = datetime.fromtimestamp(forecast['dt'])
        if forecast_date.date() == target_date.date():
            weather_description = forecast['weather'][0]['description']
            temperature = forecast['main']['temp']
            return {
                'date': target_date.strftime('%Y-%m-%d'),
                'city': city,
                'weather': weather_description,
                'temperature': temperature
            }

    return "No weather information available for the date provided."
