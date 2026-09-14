
import requests
from config import API_KEY

city = "Mumbai"

url = "https://api.openweathermap.org/data/2.5/weather"

params = {
    "q": city,
    "appid": API_KEY,
    "units": "metric"
}

response = requests.get(url, params=params)

print("Status:", response.status_code)
print("Response:")
print(response.text)

