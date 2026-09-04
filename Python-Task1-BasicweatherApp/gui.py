import tkinter as tk
import requests
import json
import os
from config import API_KEY
from datetime import datetime, timezone, timedelta
from PIL import Image, ImageDraw, ImageFont, ImageTk


# ============================================================
# VARIABLES
# ============================================================

current_temperature_c = None
current_temperature_f = None
current_min_temperature_c = None
current_max_temperature_c = None

current_unit = "C"

current_city = ""
current_humidity = 0
current_condition = ""
current_wind_speed = 0

current_feels_like_c = None
current_feels_like_f = None

current_sunrise = ""
current_sunset = ""

forecast_data = []

recent_cities = []
MAX_RECENT_CITIES = 5
HISTORY_FILE = "recent_cities.json"

emoji_cache = {}

dark_mode = False

# Current city's timezone offset from UTC
current_timezone_offset = 0


# ============================================================
# COLORS
# ============================================================

BG_COLOR = "#EAF6FF"
CARD_COLOR = "#FFFFFF"
TITLE_COLOR = "#174A7C"
TEXT_COLOR = "#263238"

BUTTON_COLOR = "#2D8CFF"
REFRESH_COLOR = "#4CAF50"
CLEAR_COLOR = "#E53935"

BUTTON_TEXT = "#FFFFFF"

FORECAST_TEXT_COLOR = "#000000"


# ============================================================
# LIGHT / DARK COLORS
# ============================================================

LIGHT_COLORS = {
    "bg": "#EAF6FF",
    "card": "#FFFFFF",
    "title": "#174A7C",
    "text": "#263238",
    "muted": "#607D8B",
}

DARK_COLORS = {
    "bg": "#18232F",
    "card": "#263544",
    "title": "#90CAF9",
    "text": "#F5F7FA",
    "muted": "#B0BEC5",
}


# ============================================================
# EMOJI SETTINGS
# ============================================================

EMOJI_FONT_PATH = r"C:\Windows\Fonts\seguiemj.ttf"

BIG_EMOJI_SIZE = 70
NORMAL_EMOJI_SIZE = 38
DAY_EMOJI_SIZE = 50


# ============================================================
# WEATHER EMOJI
# ============================================================

def get_weather_emoji(weather_id):

    if 200 <= weather_id <= 232:
        return "⛈️"

    if 300 <= weather_id <= 321:
        return "🌧️"

    if 500 <= weather_id <= 531:
        return "🌧️"

    if 600 <= weather_id <= 622:
        return "❄️"

    if 700 <= weather_id <= 781:
        return "🌫️"

    if weather_id == 800:
        return "☀️"

    if weather_id == 801:
        return "🌤️"

    if weather_id in [802, 803, 804]:
        return "☁️"

    return "☁️"


# ============================================================
# CREATE COLOR EMOJI
# ============================================================

def create_emoji_image(emoji, size):

    key = (emoji, size)

    if key in emoji_cache:
        return emoji_cache[key]

    try:

        if not os.path.exists(EMOJI_FONT_PATH):
            return None

        font = ImageFont.truetype(
            EMOJI_FONT_PATH,
            size
        )

        image = Image.new(
            "RGBA",
            (size * 2, size * 2),
            (255, 255, 255, 0)
        )

        draw = ImageDraw.Draw(image)

        try:

            draw.text(
                (10, 5),
                emoji,
                font=font,
                embedded_color=True
            )

        except TypeError:

            draw.text(
                (10, 5),
                emoji,
                font=font,
                fill="black"
            )

        photo = ImageTk.PhotoImage(image)

        emoji_cache[key] = photo

        return photo

    except Exception:

        return None


# ============================================================
# RECENT CITY HISTORY
# ============================================================

def add_recent_city(city):

    city = city.strip()

    if not city:
        return

    recent_cities[:] = [
        item
        for item in recent_cities
        if item.lower() != city.lower()
    ]

    recent_cities.insert(0, city)

    del recent_cities[MAX_RECENT_CITIES:]

    save_recent_cities()
    update_recent_cities()


def load_saved_recent_cities():

    global recent_cities

    if not os.path.exists(HISTORY_FILE):

        recent_cities = []
        return

    try:

        with open(
            HISTORY_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            saved = json.load(file)

        if isinstance(saved, list):

            recent_cities = [
                str(city).strip()
                for city in saved
                if str(city).strip()
            ][:MAX_RECENT_CITIES]

        else:

            recent_cities = []

    except (
        OSError,
        json.JSONDecodeError
    ):

        recent_cities = []


def save_recent_cities():

    try:

        with open(
            HISTORY_FILE,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                recent_cities,
                file,
                ensure_ascii=False,
                indent=2
            )

    except OSError as error:

        print(
            f"Could not save recent cities: {error}"
        )


def load_recent_city(city):

    city_entry.delete(
        0,
        tk.END
    )

    city_entry.insert(
        0,
        city
    )

    get_weather()


def clear_recent_cities():

    recent_cities.clear()

    save_recent_cities()

    update_recent_cities()


def update_recent_cities():

    for widget in recent_cities_frame.winfo_children():
        widget.destroy()

    colors = DARK_COLORS if dark_mode else LIGHT_COLORS

    title_widget = tk.Label(
        recent_cities_frame,
        text="Recent Cities",
        font=("Arial", 18, "bold"),
        bg=colors["bg"],
        fg=colors["title"]
    )

    title_widget.pack(
        pady=(5, 8)
    )

    if recent_cities:

        for city in recent_cities:

            button = tk.Button(
                recent_cities_frame,
                text=f"📍 {city}",
                font=("Arial", 12),
                width=25,
                bg=colors["card"],
                fg=colors["text"],
                activebackground="#DCEEFF",
                activeforeground="#000000",
                relief="groove",
                borderwidth=1,
                cursor="hand2",
                command=lambda c=city: load_recent_city(c)
            )

            button.pack(
                pady=3
            )

        clear_history_button = tk.Button(
            recent_cities_frame,
            text="🗑️ Clear History",
            font=("Arial", 12, "bold"),
            width=20,
            bg=CLEAR_COLOR,
            fg="white",
            activebackground="#C62828",
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            command=clear_recent_cities
        )

        clear_history_button.pack(
            pady=10
        )

    else:

        empty_label = tk.Label(
            recent_cities_frame,
            text="No recent cities",
            font=("Arial", 11, "italic"),
            bg=colors["bg"],
            fg=colors["muted"]
        )

        empty_label.pack(
            pady=5
        )


# ============================================================
# GET CITY LOCAL TIME
# ============================================================

def city_datetime(timestamp):

    try:

        utc_time = datetime.fromtimestamp(
            timestamp,
            tz=timezone.utc
        )

        city_time = (
            utc_time
            + timedelta(seconds=current_timezone_offset)
        )

        return city_time

    except (TypeError, ValueError, OSError):

        return None


# ============================================================
# GET CURRENT WEATHER
# ============================================================

def get_weather():

    global current_temperature_c
    global current_temperature_f
    global current_min_temperature_c
    global current_max_temperature_c

    global current_city
    global current_humidity
    global current_condition
    global current_wind_speed

    global current_feels_like_c
    global current_feels_like_f

    global current_sunrise
    global current_sunset

    global current_timezone_offset

    city = city_entry.get().strip()

    if not city:

        result_label.config(
            text="Please enter a city name."
        )

        return

    result_label.config(
        text="Loading weather..."
    )

    forecast_status.config(
        text=""
    )

    window.update_idletasks()

    url = (
        "https://api.openweathermap.org/data/2.5/weather"
    )

    params = {
        "q": city,
        "appid": API_KEY,
        "units": "metric"
    }

    try:

        response = requests.get(
            url,
            params=params,
            timeout=10
        )

        try:

            data = response.json()

        except ValueError:

            result_label.config(
                text="Invalid response from weather service."
            )

            return

        if response.status_code == 404:

            result_label.config(
                text="City not found. Please enter a valid city name."
            )

            last_updated_label.config(
                text=""
            )

            return

        if response.status_code == 401:

            result_label.config(
                text="Invalid API key. Check config.py."
            )

            last_updated_label.config(
                text=""
            )

            return

        if response.status_code != 200:

            result_label.config(
                text=(
                    "Weather service error. "
                    f"Code: {response.status_code}"
                )
            )

            return

        # ====================================================
        # CITY
        # ====================================================

        current_city = data.get(
            "name",
            city
        )

        current_timezone_offset = int(
            data.get(
                "timezone",
                0
            )
        )

        # ====================================================
        # MAIN DATA
        # ====================================================

        main_data = data.get(
            "main",
            {}
        )

        current_temperature_c = float(
            main_data.get(
                "temp",
                0
            )
        )

        current_temperature_f = (
            current_temperature_c * 9 / 5
        ) + 32

        current_min_temperature_c = float(
            main_data.get(
                "temp_min",
                current_temperature_c
            )
        )

        current_max_temperature_c = float(
            main_data.get(
                "temp_max",
                current_temperature_c
            )
        )

        # ====================================================
        # FEELS LIKE
        # ====================================================

        current_feels_like_c = float(
            main_data.get(
                "feels_like",
                current_temperature_c
            )
        )

        current_feels_like_f = (
            current_feels_like_c * 9 / 5
        ) + 32

        # ====================================================
        # HUMIDITY
        # ====================================================

        current_humidity = int(
            main_data.get(
                "humidity",
                0
            )
        )

        # ====================================================
        # WEATHER CONDITION
        # ====================================================

        weather_list = data.get(
            "weather",
            []
        )

        if weather_list:

            current_condition = weather_list[0].get(
                "description",
                "Unknown"
            )

            weather_id = int(
                weather_list[0].get(
                    "id",
                    800
                )
            )

        else:

            current_condition = "Unknown"
            weather_id = 800

        # ====================================================
        # WIND
        # ====================================================

        wind_data = data.get(
            "wind",
            {}
        )

        current_wind_speed = float(
            wind_data.get(
                "speed",
                0
            )
        )

        # ====================================================
        # SUNRISE / SUNSET
        # ====================================================

        system_data = data.get(
            "sys",
            {}
        )

        sunrise_timestamp = system_data.get(
            "sunrise"
        )

        sunset_timestamp = system_data.get(
            "sunset"
        )

        if sunrise_timestamp:

            sunrise_time = city_datetime(
                sunrise_timestamp
            )

            if sunrise_time:

                current_sunrise = sunrise_time.strftime(
                    "%I:%M %p"
                ).lstrip("0")

            else:

                current_sunrise = "N/A"

        else:

            current_sunrise = "N/A"

        if sunset_timestamp:

            sunset_time = city_datetime(
                sunset_timestamp
            )

            if sunset_time:

                current_sunset = sunset_time.strftime(
                    "%I:%M %p"
                ).lstrip("0")

            else:

                current_sunset = "N/A"

        else:

            current_sunset = "N/A"

        # ====================================================
        # RECENT CITY
        # ====================================================

        add_recent_city(
            current_city
        )

        # ====================================================
        # UNIT BUTTON
        # ====================================================

        if current_unit == "C":

            unit_button.config(
                text="Switch to °F"
            )

        else:

            unit_button.config(
                text="Switch to °C"
            )

        # ====================================================
        # LAST UPDATED
        # ====================================================

        update_time = datetime.now().strftime(
            "%I:%M:%S %p"
        ).lstrip("0")

        update_date = datetime.now().strftime(
            "%d %B %Y"
        )

        last_updated_label.config(
            text=(
                f"Last Updated: {update_time}\n"
                f"{update_date}"
            )
        )

        # ====================================================
        # CURRENT WEATHER ICON
        # ====================================================

        emoji = get_weather_emoji(
            weather_id
        )

        emoji_image = create_emoji_image(
            emoji,
            BIG_EMOJI_SIZE
        )

        if emoji_image:

            current_icon_label.config(
                image=emoji_image,
                text=""
            )

            current_icon_label.image = emoji_image

        else:

            current_icon_label.config(
                image="",
                text=emoji,
                font=("Segoe UI Emoji", 60)
            )

        # ====================================================
        # DISPLAY CURRENT WEATHER
        # ====================================================

        show_current_weather()

        # ====================================================
        # FORECAST
        # ====================================================

        get_forecast(
            current_city
        )

    except requests.exceptions.Timeout:

        result_label.config(
            text="Request timed out. Please try again."
        )

    except requests.exceptions.ConnectionError:

        result_label.config(
            text="No internet connection."
        )

    except requests.exceptions.RequestException as error:

        result_label.config(
            text=f"Network error: {error}"
        )

    except Exception as error:

        result_label.config(
            text=f"Error: {error}"
        )


# ============================================================
# WEATHER DETAILS
# ============================================================

weather_details_frame = None


def update_weather_details():

    if weather_details_frame is None:
        return

    for widget in weather_details_frame.winfo_children():
        widget.destroy()

    if current_temperature_c is None:
        return

    colors = DARK_COLORS if dark_mode else LIGHT_COLORS

    if current_unit == "C":

        feels_like = (
            f"{current_feels_like_c:.1f} °C"
        )

    else:

        feels_like = (
            f"{current_feels_like_f:.1f} °F"
        )

    details = [

        (
            "🌡️",
            "Feels Like",
            feels_like
        ),

        (
            "💧",
            "Humidity",
            f"{current_humidity}%"
        ),

        (
            "💨",
            "Wind Speed",
            f"{current_wind_speed:.1f} m/s"
        ),

        (
            "🌅",
            "Sunrise",
            current_sunrise
        ),

        (
            "🌇",
            "Sunset",
            current_sunset
        ),

    ]

    for icon, name, value in details:

        row = tk.Frame(
            weather_details_frame,
            bg=colors["card"]
        )

        row.pack(
            fill="x",
            pady=2
        )

        label = tk.Label(
            row,
            text=f"{icon}  {name}: {value}",
            font=("Segoe UI Emoji", 12, "bold"),
            bg=colors["card"],
            fg=colors["text"],
            anchor="w"
        )

        label.pack(
            fill="x",
            padx=10,
            pady=5
        )


# ============================================================
# WEATHER SUMMARY
# ============================================================

def update_weather_summary():

    if current_temperature_c is None:

        summary_value_label.config(
            text=(
                "Search for a city to see "
                "a weather summary."
            )
        )

        return

    if current_unit == "C":

        temperature = (
            f"{current_temperature_c:.1f} °C"
        )

        feels_like = (
            f"{current_feels_like_c:.1f} °C"
        )

    else:

        temperature = (
            f"{current_temperature_f:.1f} °F"
        )

        feels_like = (
            f"{current_feels_like_f:.1f} °F"
        )

    summary_value_label.config(

        text=(

            f"🌡️ {temperature}   |   "
            f"🌡️ Feels Like {feels_like}\n"

            f"💧 {current_humidity}% Humidity   |   "
            f"💨 {current_wind_speed:.1f} m/s Wind\n"

            f"🌅 {current_sunrise}   |   "
            f"🌇 {current_sunset}"

        )
    )


# ============================================================
# SHOW CURRENT WEATHER
# ============================================================

def show_current_weather():

    if current_temperature_c is None:
        return

    if current_unit == "C":

        temperature = (
            f"{current_temperature_c:.1f} °C"
        )

        feels_like = (
            f"{current_feels_like_c:.1f} °C"
        )

    else:

        temperature = (
            f"{current_temperature_f:.1f} °F"
        )

        feels_like = (
            f"{current_feels_like_f:.1f} °F"
        )

    result_label.config(

        text=(

            f"📍  {current_city}\n\n"

            f"🌡️  Temperature: {temperature}\n"

            f"🌡️  Feels Like: {feels_like}\n"

            f"💧  Humidity: {current_humidity}%\n"

            f"🌤️  Condition: "
            f"{current_condition.title()}\n"

            f"💨  Wind Speed: "
            f"{current_wind_speed:.1f} m/s\n"

            f"🌅  Sunrise: {current_sunrise}\n"

            f"🌇  Sunset: {current_sunset}"

        ),

        font=("Segoe UI Emoji", 15),
        justify="left"
    )

    update_weather_details()
    update_weather_summary()


# ============================================================
# SWITCH °C / °F
# ============================================================

def toggle_unit():

    global current_unit

    if current_temperature_c is None:

        result_label.config(
            text="Get weather first."
        )

        return

    if current_unit == "C":

        current_unit = "F"

        unit_button.config(
            text="Switch to °C"
        )

    else:

        current_unit = "C"

        unit_button.config(
            text="Switch to °F"
        )

    show_current_weather()
    display_forecasts()


# ============================================================
# GET FORECAST
# ============================================================

def get_forecast(city):

    global forecast_data

    url = (
        "https://api.openweathermap.org/data/2.5/forecast"
    )

    params = {
        "q": city,
        "appid": API_KEY,
        "units": "metric"
    }

    try:

        response = requests.get(
            url,
            params=params,
            timeout=10
        )

        try:

            data = response.json()

        except ValueError:

            forecast_status.config(
                text="Invalid forecast response."
            )

            return

        if response.status_code == 401:

            forecast_status.config(
                text="Invalid API key."
            )

            return

        if response.status_code != 200:

            forecast_status.config(
                text="Forecast unavailable."
            )

            return

        forecast_data = data.get(
            "list",
            []
        )

        display_forecasts()

    except requests.exceptions.Timeout:

        forecast_status.config(
            text="Forecast request timed out."
        )

    except requests.exceptions.ConnectionError:

        forecast_status.config(
            text="No internet connection."
        )

    except requests.exceptions.RequestException:

        forecast_status.config(
            text="Unable to get forecast."
        )

    except Exception as error:

        forecast_status.config(
            text=f"Forecast error: {error}"
        )


# ============================================================
# WEATHER CARD COLORS
# ============================================================

def get_weather_colors(weather_id):

    if 200 <= weather_id <= 232:
        return "#F3E5F5", "#8E44AD"

    if 300 <= weather_id <= 321:
        return "#E3F2FD", "#3498DB"

    if 500 <= weather_id <= 531:
        return "#D6ECFF", "#2980B9"

    if 600 <= weather_id <= 622:
        return "#EAF7FF", "#5DADE2"

    if 700 <= weather_id <= 781:
        return "#ECEFF1", "#78909C"

    if weather_id == 800:
        return "#FFF8D6", "#F1C40F"

    if weather_id in (801, 802):
        return "#E8F5E9", "#66BB6A"

    if weather_id in (803, 804):
        return "#F0F4F7", "#607D8B"

    return "#FFFFFF", "#B0BEC5"


# ============================================================
# CREATE FORECAST EMOJI LABEL
# ============================================================

def create_forecast_emoji_label(
    parent,
    emoji,
    size,
    bg
):

    emoji_image = create_emoji_image(
        emoji,
        size
    )

    if emoji_image:

        label = tk.Label(
            parent,
            image=emoji_image,
            bg=bg
        )

        label.image = emoji_image

    else:

        label = tk.Label(
            parent,
            text=emoji,
            font=("Segoe UI Emoji", size),
            bg=bg,
            fg=FORECAST_TEXT_COLOR
        )

    return label


# ============================================================
# DISPLAY FORECASTS
# ============================================================

def display_forecasts():

    for widget in forecast_frame.winfo_children():
        widget.destroy()

    if not forecast_data:
        return

    colors = DARK_COLORS if dark_mode else LIGHT_COLORS

    forecast_status.config(
        text=""
    )

    # ========================================================
    # NEXT 6 FORECASTS
    # ========================================================

    title_widget = tk.Label(
        forecast_frame,
        text="Next 6 Forecasts",
        font=("Arial", 20, "bold"),
        bg=colors["bg"],
        fg=colors["title"]
    )

    title_widget.pack(
        pady=15
    )

    for item in forecast_data[:6]:

        try:

            forecast_time = city_datetime(
                item["dt"]
            )

            if forecast_time is None:
                continue

            time_text = forecast_time.strftime(
                "%A %I:%M %p"
            ).lstrip("0")

            temperature_c = float(
                item["main"]["temp"]
            )

            temperature_f = (
                temperature_c * 9 / 5
            ) + 32

            if current_unit == "C":

                temperature_text = (
                    f"{temperature_c:.1f} °C"
                )

            else:

                temperature_text = (
                    f"{temperature_f:.1f} °F"
                )

            weather_items = item.get(
                "weather",
                []
            )

            if not weather_items:
                continue

            condition = weather_items[0].get(
                "description",
                "Unknown"
            )

            rain_probability = int(
                round(
                    float(
                        item.get(
                            "pop",
                            0
                        )
                    ) * 100
                )
            )

            weather_id = int(
                weather_items[0].get(
                    "id",
                    800
                )
            )

            emoji = get_weather_emoji(
                weather_id
            )

            card_bg, card_border = get_weather_colors(
                weather_id
            )

            card = tk.Frame(
                forecast_frame,
                bg=card_bg,
                relief="groove",
                borderwidth=2,
                highlightbackground=card_border,
                highlightcolor=card_border,
                highlightthickness=1
            )

            card.pack(
                fill="x",
                padx=30,
                pady=5
            )

            emoji_label = create_forecast_emoji_label(
                card,
                emoji,
                NORMAL_EMOJI_SIZE,
                card_bg
            )

            emoji_label.pack(
                side="left",
                padx=20,
                pady=8
            )

            info = tk.Label(
                card,
                text=(

                    f"{time_text}\n"

                    f"{temperature_text}   "
                    f"{condition.title()}\n"

                    f"🌧️ Rain Probability: "
                    f"{rain_probability}%"

                ),
                font=("Segoe UI Emoji", 11),
                bg=card_bg,
                fg=FORECAST_TEXT_COLOR,
                justify="left"
            )

            info.pack(
                side="left"
            )

        except (
            KeyError,
            TypeError,
            ValueError,
            OSError
        ):

            continue

    # ========================================================
    # GROUP DAYS
    # ========================================================

    days = {}

    for item in forecast_data:

        try:

            date_time = city_datetime(
                item["dt"]
            )

            if date_time is None:
                continue

            date = date_time.date()

            days.setdefault(
                date,
                []
            ).append(item)

        except (
            KeyError,
            TypeError,
            ValueError,
            OSError
        ):

            continue

    if not days:
        return

    # ========================================================
    # UPCOMING FORECAST
    # ========================================================

    upcoming_title = tk.Label(
        forecast_frame,
        text="Upcoming Forecast",
        font=("Arial", 20, "bold"),
        bg=colors["bg"],
        fg=colors["title"]
    )

    upcoming_title.pack(
        pady=20
    )

    city_now = (
        datetime.now(timezone.utc)
        + timedelta(seconds=current_timezone_offset)
    )

    today = city_now.date()

    future_days = [
        date
        for date in days
        if date >= today
    ]

    future_days.sort()

    for date in future_days[:5]:

        items = days[date]

        try:

            day_name = date.strftime(
                "%A"
            )

            best_item = min(
                items,
                key=lambda item: abs(
                    city_datetime(item["dt"]).hour - 12
                )
            )

            temperature_c = float(
                best_item["main"]["temp"]
            )

            temperature_f = (
                temperature_c * 9 / 5
            ) + 32

            if current_unit == "C":

                temperature_text = (
                    f"{temperature_c:.1f} °C"
                )

            else:

                temperature_text = (
                    f"{temperature_f:.1f} °F"
                )

            weather_items = best_item.get(
                "weather",
                []
            )

            if not weather_items:
                continue

            condition = weather_items[0].get(
                "description",
                "Unknown"
            )

            weather_id = int(
                weather_items[0].get(
                    "id",
                    800
                )
            )

            emoji = get_weather_emoji(
                weather_id
            )

            card_bg, card_border = get_weather_colors(
                weather_id
            )

            card = tk.Frame(
                forecast_frame,
                bg=card_bg,
                relief="groove",
                borderwidth=2,
                highlightbackground=card_border,
                highlightcolor=card_border,
                highlightthickness=1
            )

            card.pack(
                fill="x",
                padx=30,
                pady=5
            )

            emoji_label = create_forecast_emoji_label(
                card,
                emoji,
                NORMAL_EMOJI_SIZE,
                card_bg
            )

            emoji_label.pack(
                side="left",
                padx=20,
                pady=10
            )

            text = tk.Label(
                card,
                text=(

                    f"{day_name}\n"

                    f"{temperature_text}   "
                    f"{condition.title()}"

                ),
                font=("Arial", 12),
                bg=card_bg,
                fg=FORECAST_TEXT_COLOR,
                justify="left"
            )

            text.pack(
                side="left"
            )

        except (
            KeyError,
            TypeError,
            ValueError,
            OSError
        ):

            continue

    # ========================================================
    # 5-DAY FORECAST
    # ========================================================

    five_day_title = tk.Label(
        forecast_frame,
        text="5-Day Forecast",
        font=("Arial", 20, "bold"),
        bg=colors["bg"],
        fg=colors["title"]
    )

    five_day_title.pack(
        pady=20
    )

    for date in future_days[:5]:

        items = days[date]

        try:

            day_name = date.strftime(
                "%A"
            )

            temperatures = [
                float(item["main"]["temp"])
                for item in items
                if "main" in item
                and "temp" in item["main"]
            ]

            if not temperatures:
                continue

            minimum_c = min(
                temperatures
            )

            maximum_c = max(
                temperatures
            )

            minimum_f = (
                minimum_c * 9 / 5
            ) + 32

            maximum_f = (
                maximum_c * 9 / 5
            ) + 32

            if current_unit == "C":

                temperature_text = (

                    f"{minimum_c:.1f}°C - "
                    f"{maximum_c:.1f}°C"

                )

            else:

                temperature_text = (

                    f"{minimum_f:.1f}°F - "
                    f"{maximum_f:.1f}°F"

                )

            best_item = min(
                items,
                key=lambda item: abs(
                    city_datetime(item["dt"]).hour - 12
                )
            )

            weather_items = best_item.get(
                "weather",
                []
            )

            if not weather_items:
                continue

            condition = weather_items[0].get(
                "description",
                "Unknown"
            )

            weather_id = int(
                weather_items[0].get(
                    "id",
                    800
                )
            )

            emoji = get_weather_emoji(
                weather_id
            )

            card_bg, card_border = get_weather_colors(
                weather_id
            )

            card = tk.Frame(
                forecast_frame,
                bg=card_bg,
                relief="groove",
                borderwidth=2,
                highlightbackground=card_border,
                highlightcolor=card_border,
                highlightthickness=1
            )

            card.pack(
                fill="x",
                padx=30,
                pady=5
            )

            emoji_label = create_forecast_emoji_label(
                card,
                emoji,
                DAY_EMOJI_SIZE,
                card_bg
            )

            emoji_label.pack(
                side="left",
                padx=20,
                pady=15
            )

            information = tk.Label(
                card,
                text=(

                    f"{day_name}\n"

                    f"{temperature_text}\n"

                    f"{condition.title()}"

                ),
                font=("Arial", 12),
                bg=card_bg,
                fg=FORECAST_TEXT_COLOR,
                justify="left"
            )

            information.pack(
                side="left"
            )

        except (
            KeyError,
            TypeError,
            ValueError,
            OSError
        ):

            continue


# ============================================================
# APPLY THEME
# ============================================================

def apply_theme_to_widgets(
    widget,
    bg,
    fg=None
):

    try:

        config = widget.configure()

        if "background" in config:

            widget.configure(
                bg=bg
            )

        if (
            fg is not None
            and "foreground" in config
        ):

            widget.configure(
                fg=fg
            )

    except tk.TclError:

        pass

    for child in widget.winfo_children():

        apply_theme_to_widgets(
            child,
            bg,
            fg
        )


# ============================================================
# DARK MODE
# ============================================================

def toggle_dark_mode():

    global dark_mode
    global BG_COLOR
    global CARD_COLOR
    global TITLE_COLOR
    global TEXT_COLOR

    dark_mode = not dark_mode

    colors = (
        DARK_COLORS
        if dark_mode
        else LIGHT_COLORS
    )

    BG_COLOR = colors["bg"]
    CARD_COLOR = colors["card"]
    TITLE_COLOR = colors["title"]
    TEXT_COLOR = colors["text"]

    apply_theme_to_widgets(
        window,
        colors["bg"],
        colors["text"]
    )

    title.config(
        bg=colors["bg"],
        fg=colors["title"]
    )

    city_label.config(
        bg=colors["bg"],
        fg=colors["text"]
    )

    recent_cities_frame.config(
        bg=colors["bg"]
    )

    forecast_frame.config(
        bg=colors["bg"]
    )

    forecast_status.config(
        bg=colors["bg"],
        fg=colors["text"]
    )

    last_updated_label.config(
        bg=colors["bg"],
        fg=colors["muted"]
    )

    current_icon_label.config(
        bg=colors["bg"]
    )

    result_card.config(
        bg=colors["card"]
    )

    result_label.config(
        bg=colors["card"],
        fg=colors["text"]
    )

    weather_details_frame.config(
        bg=colors["card"]
    )

    summary_card.config(
        bg=colors["card"]
    )

    summary_label.config(
        bg=colors["card"],
        fg=colors["title"]
    )

    summary_value_label.config(
        bg=colors["card"],
        fg=colors["text"]
    )

    dark_mode_button.config(
        text=(
            "☀️ Light Mode"
            if dark_mode
            else "🌙 Dark Mode"
        )
    )

    update_recent_cities()
    update_weather_details()
    display_forecasts()


# ============================================================
# AUTOMATIC UPDATE
# ============================================================

def automatic_update():

    if current_city:

        get_weather()

    window.after(
        3600000,
        automatic_update
    )


# ============================================================
# MAIN WINDOW
# ============================================================

window = tk.Tk()

window.title(
    "Weather App"
)

window.geometry(
    "850x900"
)

window.minsize(
    650,
    700
)

window.configure(
    bg=BG_COLOR
)


# ============================================================
# SCROLL AREA
# ============================================================

canvas = tk.Canvas(
    window,
    bg=BG_COLOR,
    highlightthickness=0
)

scrollbar = tk.Scrollbar(
    window,
    orient="vertical",
    command=canvas.yview
)

scrollable_frame = tk.Frame(
    canvas,
    bg=BG_COLOR
)

scrollable_frame.bind(
    "<Configure>",
    lambda event: canvas.configure(
        scrollregion=canvas.bbox("all")
    )
)

canvas_window = canvas.create_window(
    (0, 0),
    window=scrollable_frame,
    anchor="nw",
    width=820
)

canvas.configure(
    yscrollcommand=scrollbar.set
)


def resize_scrollable_frame(event):

    canvas.itemconfig(
        canvas_window,
        width=max(
            event.width,
            600
        )
    )


canvas.bind(
    "<Configure>",
    resize_scrollable_frame
)


# ============================================================
# MOUSE WHEEL
# ============================================================

def on_mousewheel(event):

    canvas.yview_scroll(
        int(-1 * (event.delta / 120)),
        "units"
    )


canvas.bind_all(
    "<MouseWheel>",
    on_mousewheel
)

canvas.pack(
    side="left",
    fill="both",
    expand=True
)

scrollbar.pack(
    side="right",
    fill="y"
)


# ============================================================
# TITLE
# ============================================================

title = tk.Label(
    scrollable_frame,
    text="🌤️ Weather App",
    font=("Arial", 30, "bold"),
    bg=BG_COLOR,
    fg=TITLE_COLOR
)

title.pack(
    pady=25
)


# ============================================================
# CITY LABEL
# ============================================================

city_label = tk.Label(
    scrollable_frame,
    text="Enter city name",
    font=("Arial", 16, "bold"),
    bg=BG_COLOR,
    fg=TEXT_COLOR
)

city_label.pack()


# ============================================================
# CITY ENTRY
# ============================================================

city_entry = tk.Entry(
    scrollable_frame,
    font=("Arial", 16),
    width=30,
    justify="center"
)

city_entry.pack(
    pady=10
)

city_entry.bind(
    "<Return>",
    lambda event: get_weather()
)


# ============================================================
# RECENT CITIES
# ============================================================

recent_cities_frame = tk.Frame(
    scrollable_frame,
    bg=BG_COLOR
)

recent_cities_frame.pack(
    fill="x",
    pady=5
)

load_saved_recent_cities()
update_recent_cities()


# ============================================================
# SEARCH BUTTON
# ============================================================

weather_button = tk.Button(
    scrollable_frame,
    text="🔍 Search",
    font=("Arial", 14, "bold"),
    width=18,
    bg=BUTTON_COLOR,
    fg=BUTTON_TEXT,
    activebackground="#176FCC",
    activeforeground="white",
    relief="flat",
    cursor="hand2",
    command=get_weather
)

weather_button.pack(
    pady=8
)


# ============================================================
# REFRESH BUTTON
# ============================================================

refresh_button = tk.Button(
    scrollable_frame,
    text="🔄 Refresh Weather",
    font=("Arial", 13, "bold"),
    width=18,
    bg=REFRESH_COLOR,
    fg=BUTTON_TEXT,
    activebackground="#388E3C",
    activeforeground="white",
    relief="flat",
    cursor="hand2",
    command=get_weather
)

refresh_button.pack(
    pady=5
)


# ============================================================
# CURRENT WEATHER ICON
# ============================================================

current_icon_label = tk.Label(
    scrollable_frame,
    bg=BG_COLOR
)

current_icon_label.pack(
    pady=10
)


# ============================================================
# CURRENT WEATHER CARD
# ============================================================

result_card = tk.Frame(
    scrollable_frame,
    bg=CARD_COLOR,
    relief="groove",
    borderwidth=1
)

result_card.pack(
    fill="x",
    padx=80,
    pady=10
)


result_label = tk.Label(
    result_card,
    text="Enter a city to see the weather.",
    font=("Segoe UI Emoji", 15),
    bg=CARD_COLOR,
    fg=TEXT_COLOR,
    justify="left"
)

result_label.pack(
    padx=30,
    pady=20
)


# ============================================================
# WEATHER DETAILS
# ============================================================

weather_details_frame = tk.Frame(
    result_card,
    bg=CARD_COLOR
)

weather_details_frame.pack(
    fill="x",
    padx=20,
    pady=(0, 15)
)


# ============================================================
# WEATHER SUMMARY
# ============================================================

summary_card = tk.Frame(
    result_card,
    bg="#E8F4FF",
    relief="groove",
    borderwidth=1
)

summary_card.pack(
    fill="x",
    padx=20,
    pady=(0, 18)
)


summary_label = tk.Label(
    summary_card,
    text="🌤️ Weather Summary",
    font=("Segoe UI Emoji", 14, "bold"),
    bg="#E8F4FF",
    fg=TITLE_COLOR
)

summary_label.pack(
    pady=(10, 5)
)


summary_value_label = tk.Label(
    summary_card,
    text=(
        "Search for a city to see "
        "a weather summary."
    ),
    font=("Segoe UI Emoji", 11),
    bg="#E8F4FF",
    fg=TEXT_COLOR,
    justify="center"
)

summary_value_label.pack(
    padx=10,
    pady=(2, 10)
)


# ============================================================
# LAST UPDATED
# ============================================================

last_updated_label = tk.Label(
    scrollable_frame,
    text="",
    font=("Arial", 11, "italic"),
    bg=BG_COLOR,
    fg="#607D8B",
    justify="center"
)

last_updated_label.pack(
    pady=5
)


# ============================================================
# DARK MODE BUTTON
# ============================================================

dark_mode_button = tk.Button(
    scrollable_frame,
    text="🌙 Dark Mode",
    font=("Arial", 13, "bold"),
    width=18,
    bg="#455A64",
    fg="white",
    activebackground="#37474F",
    activeforeground="white",
    relief="flat",
    cursor="hand2",
    command=toggle_dark_mode
)

dark_mode_button.pack(
    pady=5
)


# ============================================================
# UNIT BUTTON
# ============================================================

unit_button = tk.Button(
    scrollable_frame,
    text="Switch to °F",
    font=("Arial", 13, "bold"),
    width=18,
    bg=BUTTON_COLOR,
    fg=BUTTON_TEXT,
    activebackground="#176FCC",
    activeforeground="white",
    relief="flat",
    cursor="hand2",
    command=toggle_unit
)

unit_button.pack(
    pady=10
)


# ============================================================
# FORECAST STATUS
# ============================================================

forecast_status = tk.Label(
    scrollable_frame,
    text="",
    font=("Arial", 11),
    bg=BG_COLOR,
    fg=TEXT_COLOR
)

forecast_status.pack()


# ============================================================
# FORECAST FRAME
# ============================================================

forecast_frame = tk.Frame(
    scrollable_frame,
    bg=BG_COLOR
)

forecast_frame.pack(
    fill="x",
    pady=10
)


# ============================================================
# AUTOMATIC UPDATE
# ============================================================

window.after(
    3600000,
    automatic_update
)


# ============================================================
# START APP
# ============================================================

window.mainloop()