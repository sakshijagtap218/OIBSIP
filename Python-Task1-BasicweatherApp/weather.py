import requests
from config import API_KEY

print("🌦️ Weather App")

location = input("Enter city name or ZIP code: ").strip()

if location == "":
    print("❌ City name or ZIP code cannot be empty.")
    exit()

# Check whether the user entered a ZIP code
if location.isdigit():

    country_code = input("Enter country code (example: US, IN, GB): ").strip().upper()

    if country_code == "":
        print("❌ Country code cannot be empty.")
        exit()

    url = (
        f"https://api.openweathermap.org/data/2.5/weather"
        f"?zip={location},{country_code}"
        f"&appid={API_KEY}&units=metric"
    )

else:
    # User entered a city name
    url = (
        f"https://api.openweathermap.org/data/2.5/weather"
        f"?q={location}"
        f"&appid={API_KEY}&units=metric"
    )

try:
    response = requests.get(url, timeout=10)

    data = response.json()

    if response.status_code == 404:
        print("❌ Location not found. Please check your input.")
        exit()

    if response.status_code == 401:
        print("❌ Invalid API key.")
        exit()

    if response.status_code != 200:
        print("❌ Something went wrong. Please try again.")
        exit()

    # Get weather information
    city_name = data["name"]
    temperature = data["main"]["temp"]
    humidity = data["main"]["humidity"]
    condition = data["weather"][0]["description"]
    wind_speed = data["wind"]["speed"]

    # Celsius to Fahrenheit
    fahrenheit = (temperature * 9 / 5) + 32

    # Display weather
    print("\n----- Weather Report -----")

    print("City:", city_name)
    print("Temperature:", round(temperature, 2), "°C")
    print("Temperature:", round(fahrenheit, 2), "°F")
    print("Humidity:", humidity, "%")
    print("Condition:", condition.title())
    print("Wind Speed:", wind_speed, "m/s")

except requests.exceptions.Timeout:
    print("❌ Request timed out. Please try again.")

except requests.exceptions.ConnectionError:
    print("❌ No internet connection.")

except requests.exceptions.RequestException:
    print("❌ Unable to connect to the weather service.")