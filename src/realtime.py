import openmeteo_requests
import requests_cache
import pandas as pd
from retry_requests import retry
from datetime import datetime

# Setup the Open-Meteo API client with cache and retry on error
cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
openmeteo = openmeteo_requests.Client(session=retry_session)

# Weather code descriptions
weather_code_description = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Drizzle: Light intensity",
    53: "Drizzle: Moderate intensity",
    55: "Drizzle: Dense intensity",
    56: "Freezing Drizzle: Light intensity",
    57: "Freezing Drizzle: Dense intensity",
    61: "Rain: Slight intensity",
    63: "Rain: Moderate intensity",
    65: "Rain: Heavy intensity",
    66: "Freezing Rain: Light intensity",
    67: "Freezing Rain: Heavy intensity",
    71: "Snow fall: Slight intensity",
    73: "Snow fall: Moderate intensity",
    75: "Snow fall: Heavy intensity",
    77: "Snow grains",
    80: "Rain showers: Slight intensity",
    81: "Rain showers: Moderate intensity",
    82: "Rain showers: Violent intensity",
    85: "Snow showers: Slight intensity",
    86: "Snow showers: Heavy intensity",
    95: "Thunderstorm: Slight or moderate",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail"
}

def get_current_weather(latitude, longitude):
    # Make sure all required weather variables are listed here
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": ["temperature_2m", "relative_humidity_2m", "weather_code"]
    }
    responses = openmeteo.weather_api("https://api.open-meteo.com/v1/forecast", params=params)
    
    # Process the first location
    response = responses[0]
    
    # Process hourly data
    hourly = response.Hourly()
    hourly_temperature = hourly.Variables(0).ValuesAsNumpy()  # Index 0 for temperature_2m
    hourly_humidity = hourly.Variables(1).ValuesAsNumpy()  # Index 1 for relative_humidity_2m
    hourly_weather_code = hourly.Variables(2).ValuesAsNumpy()  # Index 2 for weather_code

    # Prepare the DataFrame
    hourly_data = {
        "date": pd.date_range(
            start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
            end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
            freq=pd.Timedelta(seconds=hourly.Interval()),
            inclusive="left"
        ),
        "temperature": hourly_temperature,
        "humidity": hourly_humidity,
        "weather_code": hourly_weather_code
    }
    
    # Create DataFrame
    hourly_dataframe = pd.DataFrame(data=hourly_data)

    # Get the current system time
    current_time = datetime.now()
    current_hour = pd.Timestamp.now(tz='UTC').floor('h')  # Get the start of the current UTC hour
    
    # Filter for the current hour and make a copy to avoid SettingWithCopyWarning
    current_hour_data = hourly_dataframe[hourly_dataframe['date'] == current_hour].copy()

    if current_hour_data.empty:
        return {
            "current_date": current_time.strftime('%d-%m-%Y'),
            "current_time": current_time.strftime('%I:%M %p'),  # 12-hour format with AM/PM
            "current_day": current_time.strftime('%A'),
            "weather_description": "No data available for the current hour.",
            "temperature": None,
            "humidity": None
        }

    # Safely assign the weather description
    current_hour_data['weather_description'] = current_hour_data['weather_code'].map(weather_code_description)

    # Extract relevant information
    weather_object = {
        "current_date": current_time.strftime('%d-%m-%Y'),
        "current_time": current_time.strftime('%I:%M %p'),  # 12-hour format with AM/PM
        "current_day": current_time.strftime('%A'),
        "weather_description": current_hour_data['weather_description'].iloc[0],
        "temperature": current_hour_data['temperature'].iloc[0],
        "humidity": current_hour_data['humidity'].iloc[0],
        "current_location": "Kollam"
    }

    # Return the dictionary object
    return weather_object

