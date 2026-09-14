# ============================================================
# MY VOICE ASSISTANT - FINAL VERSION
# ============================================================
#
# Features:
# - Wake word
# - Speech recognition
# - Text to speech
# - NLP intent recognition
# - General knowledge Q&A
# - Wikipedia + OpenAI fallback
# - Weather
# - News
# - Email
# - Calculator
# - Google search
# - YouTube
# - Websites
# - Windows applications
# - Windows folders
# - Volume control
# - System control
# - Voice reminders
# - JSON custom commands
#
# ============================================================

import speech_recognition as sr
import pyttsx3
import datetime
import webbrowser
import subprocess
import urllib.parse
import requests
import ast
import operator
import math
import threading
import time
import re
import os
import ctypes
import smtplib
import json

from email.message import EmailMessage

from config import (
    API_KEY,
    NEWS_API_KEY,
    OPENAI_API_KEY,
    EMAIL_ADDRESS,
    EMAIL_APP_PASSWORD,
    DEFAULT_EMAIL_TO
)

# ============================================================
# SETTINGS
# ============================================================

MIC_INDEX = 2
LANGUAGE = "en-IN"
WAKE_WORD = "hey assistant"

NEWS_COUNTRY = "in"
NEWS_LIMIT = 5

CUSTOM_COMMANDS_FILE = "commands.json"

OPENAI_MODEL = "gpt-5.6-luna"

# ============================================================
# GLOBAL VARIABLES
# ============================================================

assistant_paused = False
reminder_active = False
reminder_message = ""

speak_lock = threading.Lock()

# ============================================================
# TEXT TO SPEECH
# ============================================================

def speak(text):

    if not text:
        return

    print()
    print("Assistant:", text)

    try:

        with speak_lock:

            engine = pyttsx3.init()

            engine.setProperty(
                "rate",
                170
            )

            engine.setProperty(
                "volume",
                1.0
            )

            engine.say(
                str(text)
            )

            engine.runAndWait()

            engine.stop()

    except Exception as e:

        print(
            "TTS error:",
            e
        )


# ============================================================
# SPEECH RECOGNIZER
# ============================================================

def create_recognizer():

    recognizer = sr.Recognizer()

    recognizer.energy_threshold = 300

    recognizer.dynamic_energy_threshold = True

    recognizer.pause_threshold = 0.8

    recognizer.phrase_threshold = 0.2

    recognizer.non_speaking_duration = 0.5

    return recognizer


# ============================================================
# LISTEN
# ============================================================

def listen(
    timeout=10,
    phrase_time_limit=7,
    answer_mode=False
):

    global assistant_paused

    if assistant_paused:
        return ""

    recognizer = create_recognizer()

    try:

        with sr.Microphone(
            device_index=MIC_INDEX
        ) as source:

            if answer_mode:

                print()
                print(
                    "Listening for answer..."
                )

            else:

                print()
                print(
                    "Listening..."
                )

            # Adjust microphone sensitivity
            recognizer.adjust_for_ambient_noise(
                source,
                duration=0.5
            )

            if assistant_paused:
                return ""

            try:

                audio = recognizer.listen(
                    source,
                    timeout=timeout,
                    phrase_time_limit=phrase_time_limit
                )

            except sr.WaitTimeoutError:

                print(
                    "Listening timeout."
                )

                return ""

        print(
            "Recognizing..."
        )

        try:

            result = recognizer.recognize_google(
                audio,
                language=LANGUAGE
            )

            result = result.lower().strip()

            print(
                "You said:",
                result
            )

            return result

        except sr.UnknownValueError:

            print(
                "Could not understand audio."
            )

            return ""

        except sr.RequestError:

            speak(
                "Speech recognition service is not available."
            )

            return ""

    except Exception as e:

        print(
            "Microphone error:",
            e
        )

        return ""


# ============================================================
# LISTEN AFTER ASSISTANT ASKS QUESTION
# ============================================================

def listen_after_wake():

    return listen(
        timeout=15,
        phrase_time_limit=15,
        answer_mode=True
    )


# ============================================================
# LISTEN WITH RETRY
# ============================================================

def listen_with_retry(
    question,
    attempts=3
):

    for attempt in range(attempts):

        speak(
            question
        )

        answer = listen_after_wake()

        if answer:
            return answer

        if attempt < attempts - 1:

            speak(
                "Please try again."
            )

    return ""


# ============================================================
# WAKE WORD
# ============================================================

def wait_for_wake_word():

    while True:

        print()
        print(
            "Waiting for wake word..."
        )

        command = listen(
            timeout=10,
            phrase_time_limit=5
        )

        if not command:
            continue

        if WAKE_WORD in command:

            return command

        print(
            "Wake word not detected."
        )


# ============================================================
# NLP INTENT RECOGNITION
# ============================================================

INTENT_PATTERNS = {

    "greeting": [
        r"^(hi|hello|hey)( assistant)?$"
    ],

    "time": [
        r"\bwhat is the time\b",
        r"\bwhat's the time\b",
        r"\bcurrent time\b",
        r"\btell me the time\b",
        r"^time$"
    ],

    "date": [
        r"\bwhat is the date\b",
        r"\bwhat's the date\b",
        r"\btoday's date\b",
        r"\btoday date\b",
        r"\btell me the date\b",
        r"^date$"
    ],

    "weather": [
        r"\bweather\b",
        r"\btemperature\b"
    ],

    "news": [
        r"\bnews\b",
        r"\bheadlines\b"
    ],

    "email": [
        r"\bsend email\b",
        r"\bsend an email\b",
        r"\bcompose email\b",
        r"\bwrite email\b"
    ],

    "reminder": [
        r"^remind me\b"
    ],

    "calculator": [
        r"\bsquare root\b",
        r"\bcube root\b",
        r"\bsquared\b",
        r"\bcubed\b",
        r"\bplus\b",
        r"\bminus\b",
        r"\btimes\b",
        r"\bmultiplied by\b",
        r"\bdivided by\b",
        r"\bdivide by\b",
        r"\bcalculate\b",
        r"\bmodulo\b",
        r"\bto the power of\b"
    ],

    "google_search": [
        r"^search "
    ],

    "youtube": [
        r"\byoutube\b",
        r"^play "
    ],

    "open_app": [
        r"\bopen notepad\b",
        r"\bopen calculator\b",
        r"\bopen calc\b",
        r"\bopen cmd\b",
        r"\bopen command prompt\b",
        r"\bopen file explorer\b",
        r"\bopen explorer\b"
    ],

    "system": [
        r"\block computer\b",
        r"\block pc\b",
        r"\block system\b",
        r"\bshutdown\b",
        r"\brestart\b",
        r"\bvolume up\b",
        r"\bvolume down\b",
        r"\bmute\b",
        r"\bunmute\b"
    ],

    "ai": [
        r"^ask ai ",
        r"^ai ",
        r"^ask chatgpt ",
        r"^chatgpt ",
        r"^ask assistant "
    ],

    "general_knowledge": [
        r"^what is ",
        r"^what are ",
        r"^who is ",
        r"^who was ",
        r"^where is ",
        r"^when was ",
        r"^why is ",
        r"^why are ",
        r"^how does ",
        r"^how do ",
        r"^explain "
    ]
}


def detect_intent(command):

    command = command.lower().strip()

    # ========================================================
    # CALCULATOR PRIORITY
    # ========================================================

    calculator_words = [
        "plus",
        "minus",
        "times",
        "multiplied by",
        "multiply by",
        "divided by",
        "divide by",
        "square root",
        "cube root",
        "squared",
        "cubed",
        "calculate",
        "modulo",
        "mod",
        "to the power of"
    ]

    if any(
        word in command
        for word in calculator_words
    ):

        return "calculator"

    # x multiplication

    if re.search(
        r"\d+(?:\.\d+)?\s*x\s*\d+(?:\.\d+)?",
        command
    ):

        return "calculator"

    # * multiplication

    if re.search(
        r"\d+(?:\.\d+)?\s*\*\s*\d+(?:\.\d+)?",
        command
    ):

        return "calculator"

    # Numeric "what is"

    if re.search(
        r"^what is\s+\d",
        command
    ):

        return "calculator"

    # Numeric calculate

    if re.search(
        r"^calculate\s+\d",
        command
    ):

        return "calculator"

    # ========================================================
    # OTHER INTENTS
    # ========================================================

    for intent, patterns in INTENT_PATTERNS.items():

        for pattern in patterns:

            if re.search(
                pattern,
                command
            ):

                return intent

    return "unknown"


# ============================================================
# TIME
# ============================================================

def time_command():

    current_time = datetime.datetime.now().strftime(
        "%I:%M %p"
    )

    speak(
        f"The current time is {current_time}"
    )


# ============================================================
# DATE
# ============================================================

def date_command():

    current_date = datetime.datetime.now().strftime(
        "%d %B %Y"
    )

    speak(
        f"Today's date is {current_date}"
    )


# ============================================================
# GREETING
# ============================================================

def greeting_command(command):

    greetings = [
        "hello",
        "hi",
        "hey",
        "hello assistant",
        "hi assistant",
        "hey assistant"
    ]

    if command in greetings:

        speak(
            "Hello! How can I help you?"
        )

        return True

    return False


# ============================================================
# WEATHER - FIXED
# ============================================================

def get_weather(city):

    if not city:
        return None

    try:

        # Correct OpenWeatherMap API URL
        url = "https://api.openweathermap.org/data/2.5/weather"

        params = {
            "q": city,
            "appid": API_KEY,
            "units": "metric"
        }

        response = requests.get(
            url,
            params=params,
            timeout=10
        )

        data = response.json()

        if response.status_code != 200:

            print(
                "Weather API error:",
                data
            )

            return None

        return data

    except requests.exceptions.Timeout:

        print(
            "Weather API timeout."
        )

        return None

    except requests.exceptions.RequestException as e:

        print(
            "Weather request error:",
            e
        )

        return None

    except Exception as e:

        print(
            "Weather error:",
            e
        )

        return None


def weather_command(command):

    command = command.lower().strip()

    city = None

    # --------------------------------------------------------
    # Weather patterns
    # --------------------------------------------------------

    patterns = [

        r"weather in (.+)",

        r"weather of (.+)",

        r"temperature in (.+)",

        r"temperature of (.+)",

        r"what is the weather in (.+)",

        r"what's the weather in (.+)",

        r"what is the temperature in (.+)",

        r"what's the temperature in (.+)",

        r"tell me the weather in (.+)",

        r"tell me the temperature in (.+)"

    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            command
        )

        if match:

            city = match.group(1).strip()

            break

    # --------------------------------------------------------
    # Ask city if not provided
    # --------------------------------------------------------

    if not city:

        city = listen_with_retry(
            "Which city would you like the weather for?"
        )

    if not city:

        speak(
            "Weather request cancelled."
        )

        return True

    city = city.strip()

    print(
        "Weather city:",
        city
    )

    # --------------------------------------------------------
    # API
    # --------------------------------------------------------

    data = get_weather(
        city
    )

    if not data:

        speak(
            f"Sorry, I could not find weather information "
            f"for {city}."
        )

        return True

    # --------------------------------------------------------
    # Read response safely
    # --------------------------------------------------------

    try:

        city_name = data.get(
            "name",
            city
        )

        main_data = data.get(
            "main",
            {}
        )

        weather_data = data.get(
            "weather",
            [{}]
        )

        temperature = main_data.get(
            "temp"
        )

        feels_like = main_data.get(
            "feels_like"
        )

        humidity = main_data.get(
            "humidity"
        )

        description = weather_data[0].get(
            "description",
            "unknown"
        )

        if temperature is None:

            speak(
                "Sorry, weather temperature is unavailable."
            )

            return True

        # ----------------------------------------------------
        # Console output
        # ----------------------------------------------------

        print()
        print(
            "========================================"
        )
        print(
            "WEATHER INFORMATION"
        )
        print(
            "========================================"
        )
        print(
            "City:",
            city_name
        )
        print(
            "Temperature:",
            temperature,
            "°C"
        )
        print(
            "Feels Like:",
            feels_like,
            "°C"
        )
        print(
            "Humidity:",
            humidity,
            "%"
        )
        print(
            "Condition:",
            description
        )
        print(
            "========================================"
        )

        # ----------------------------------------------------
        # Voice response
        # ----------------------------------------------------

        weather_text = (
            f"The weather in {city_name} is {description}. "
            f"The temperature is {temperature:.1f} degrees Celsius. "
        )

        if feels_like is not None:

            weather_text += (
                f"It feels like {feels_like:.1f} degrees. "
            )

        if humidity is not None:

            weather_text += (
                f"Humidity is {humidity} percent."
            )

        speak(
            weather_text
        )

    except Exception as e:

        print(
            "Weather formatting error:",
            e
        )

        speak(
            "I received the weather data, "
            "but I could not read it correctly."
        )

    return True


# ============================================================
# NEWS
# ============================================================

def get_news(
    category=None,
    keyword=None
):

    try:

        url = "https://newsapi.org/v2/top-headlines"

        params = {
            "apiKey": NEWS_API_KEY,
            "country": NEWS_COUNTRY,
            "pageSize": NEWS_LIMIT
        }

        if category:
            params["category"] = category

        if keyword:
            params["q"] = keyword

        response = requests.get(
            url,
            params=params,
            timeout=10
        )

        data = response.json()

        if response.status_code != 200:

            print(
                "News API error:",
                data
            )

            return []

        return data.get(
            "articles",
            []
        )

    except Exception as e:

        print(
            "News error:",
            e
        )

        return []


def news_command(command):

    category = None
    keyword = None

    category_map = {

        "technology news": "technology",
        "tech news": "technology",
        "sports news": "sports",
        "business news": "business",
        "entertainment news": "entertainment",
        "health news": "health",
        "science news": "science"

    }

    for phrase, value in category_map.items():

        if phrase in command:

            category = value

            break

    if command.startswith(
        "news about "
    ):

        keyword = command[
            len("news about "):
        ].strip()

    elif command.startswith(
        "news on "
    ):

        keyword = command[
            len("news on "):
        ].strip()

    articles = get_news(
        category=category,
        keyword=keyword
    )

    if not articles:

        speak(
            "Sorry, I could not get the latest news."
        )

        return True

    speak(
        "Here are the latest news headlines."
    )

    count = 0

    for article in articles:

        title = article.get(
            "title"
        )

        if not title:
            continue

        if title == "[Removed]":
            continue

        count += 1

        print(
            f"{count}. {title}"
        )

        speak(
            f"News {count}. {title}"
        )

        if count >= NEWS_LIMIT:
            break

    return True


# ============================================================
# WIKIPEDIA GENERAL KNOWLEDGE
# ============================================================

def clean_wikipedia_question(question):

    question = question.lower().strip()

    prefixes = [

        "what is ",
        "what are ",
        "who is ",
        "who was ",
        "where is ",
        "when was ",
        "why is ",
        "why are ",
        "how does ",
        "how do ",
        "explain "

    ]

    for prefix in prefixes:

        if question.startswith(prefix):

            question = question[
                len(prefix):
            ].strip()

            break

    question = question.rstrip("?").strip()

    return question


def wikipedia_answer(question):

    topic = clean_wikipedia_question(
        question
    )

    if not topic:
        return None

    headers = {
        "User-Agent":
            "MyVoiceAssistant/1.0"
    }

    # --------------------------------------------------------
    # Direct Wikipedia summary
    # --------------------------------------------------------

    try:

        encoded_topic = urllib.parse.quote(
            topic.replace(" ", "_")
        )

        url = (
            "https://en.wikipedia.org/api/rest_v1/page/summary/"
            + encoded_topic
        )

        response = requests.get(
            url,
            headers=headers,
            timeout=8
        )

        if response.status_code == 200:

            data = response.json()

            answer = data.get(
                "extract"
            )

            if answer:

                return answer

    except Exception as e:

        print(
            "Wikipedia direct lookup error:",
            e
        )

    # --------------------------------------------------------
    # Wikipedia search fallback
    # --------------------------------------------------------

    try:

        search_url = (
            "https://en.wikipedia.org/w/api.php"
        )

        params = {

            "action": "query",
            "list": "search",
            "srsearch": topic,
            "format": "json",
            "utf8": 1,
            "srlimit": 1

        }

        response = requests.get(
            search_url,
            params=params,
            headers=headers,
            timeout=8
        )

        if response.status_code != 200:
            return None

        data = response.json()

        search_results = data.get(
            "query",
            {}
        ).get(
            "search",
            []
        )

        if not search_results:
            return None

        title = search_results[0].get(
            "title"
        )

        if not title:
            return None

        encoded_title = urllib.parse.quote(
            title.replace(" ", "_")
        )

        summary_url = (
            "https://en.wikipedia.org/api/rest_v1/page/summary/"
            + encoded_title
        )

        summary_response = requests.get(
            summary_url,
            headers=headers,
            timeout=8
        )

        if summary_response.status_code != 200:
            return None

        summary_data = summary_response.json()

        return summary_data.get(
            "extract"
        )

    except Exception as e:

        print(
            "Wikipedia search error:",
            e
        )

        return None


# ============================================================
# OPENAI
# ============================================================

def openai_answer(question):

    if not OPENAI_API_KEY:

        print(
            "OpenAI API key not configured."
        )

        return None

    try:

        from openai import OpenAI

        client = OpenAI(
            api_key=OPENAI_API_KEY
        )

        response = client.responses.create(
            model=OPENAI_MODEL,
            input=(
                "Answer this question clearly and briefly "
                "for a voice assistant: "
                + question
            )
        )

        answer = response.output_text.strip()

        if answer:
            return answer

    except Exception as e:

        print(
            "OpenAI error:",
            e
        )

    return None


# ============================================================
# GENERAL KNOWLEDGE
# ============================================================

def general_knowledge_command(command):

    question = command.strip()

    answer = wikipedia_answer(
        question
    )

    if not answer:

        answer = openai_answer(
            question
        )

    if not answer:

        speak(
            "Sorry, I could not find a reliable answer."
        )

        return True

    if len(answer) > 1000:

        answer = (
            answer[:1000]
            .rsplit(" ", 1)[0]
            + "."
        )

    print()
    print(
        "Knowledge:",
        answer
    )

    speak(
        answer
    )

    return True


# ============================================================
# AI COMMAND
# ============================================================

def ai_command(command):

    prefixes = [

        "ask ai ",
        "ai ",
        "ask chatgpt ",
        "chatgpt ",
        "ask assistant "

    ]

    question = None

    for prefix in prefixes:

        if command.startswith(prefix):

            question = command[
                len(prefix):
            ].strip()

            break

    if not question:
        return False

    answer = openai_answer(
        question
    )

    if not answer:

        speak(
            "Sorry, I could not connect to the AI service."
        )

        return True

    print()
    print(
        "AI:",
        answer
    )

    speak(
        answer
    )

    return True


# ============================================================
# EMAIL
# ============================================================

def send_email(
    receiver,
    subject,
    body
):

    try:

        message = EmailMessage()

        message["From"] = EMAIL_ADDRESS
        message["To"] = receiver
        message["Subject"] = subject

        message.set_content(
            body
        )

        with smtplib.SMTP_SSL(
            "smtp.gmail.com",
            465
        ) as server:

            server.login(
                EMAIL_ADDRESS,
                EMAIL_APP_PASSWORD
            )

            server.send_message(
                message
            )

        return True

    except Exception as e:

        print(
            "Email error:",
            e
        )

        return False


def email_command(command):

    receiver = ""

    if command.startswith(
        "send email to "
    ):

        receiver = command[
            len("send email to "):
        ].strip()

    if not receiver:

        receiver = listen_with_retry(
            "Who should I send the email to? "
            "Say default email for the saved receiver."
        )

    if receiver in [
        "default",
        "default email",
        "default receiver"
    ]:

        receiver = DEFAULT_EMAIL_TO

    if not receiver:

        speak(
            "Email cancelled."
        )

        return True

    subject = listen_with_retry(
        "What is the subject?"
    )

    if not subject:

        speak(
            "Email cancelled."
        )

        return True

    body = listen_with_retry(
        "What should I write in the email?"
    )

    if not body:

        speak(
            "Email cancelled."
        )

        return True

    speak(
        f"I will send the email to {receiver}. "
        f"The subject is {subject}. "
        f"The message is {body}. "
        f"Should I send it?"
    )

    confirmation = listen_after_wake()

    if confirmation in [

        "yes",
        "yes send it",
        "send it",
        "confirm",
        "okay",
        "ok",
        "yes please"

    ]:

        success = send_email(
            receiver,
            subject,
            body
        )

        if success:

            speak(
                "Email sent successfully."
            )

        else:

            speak(
                "Sorry, I could not send the email."
            )

    else:

        speak(
            "Email cancelled."
        )

    return True


# ============================================================
# SAFE CALCULATOR - FIXED
# ============================================================

ALLOWED_OPERATORS = {

    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod

}


def safe_calculate(node):

    # --------------------------------------------------------
    # Expression
    # --------------------------------------------------------

    if isinstance(
        node,
        ast.Expression
    ):

        return safe_calculate(
            node.body
        )

    # --------------------------------------------------------
    # Number
    # --------------------------------------------------------

    if isinstance(
        node,
        ast.Constant
    ):

        if isinstance(
            node.value,
            (int, float)
        ):

            if not math.isfinite(
                float(node.value)
            ):

                raise ValueError(
                    "Invalid number"
                )

            return node.value

        raise ValueError(
            "Invalid number"
        )

    # --------------------------------------------------------
    # Binary operation
    # --------------------------------------------------------

    if isinstance(
        node,
        ast.BinOp
    ):

        left = safe_calculate(
            node.left
        )

        right = safe_calculate(
            node.right
        )

        operator_type = type(
            node.op
        )

        if operator_type not in ALLOWED_OPERATORS:

            raise ValueError(
                "Operator not allowed"
            )

        # Protect against very large powers
        if isinstance(
            node.op,
            ast.Pow
        ):

            if abs(right) > 100:

                raise ValueError(
                    "Power too large"
                )

            if abs(left) > 1000000:

                raise ValueError(
                    "Number too large"
                )

        return ALLOWED_OPERATORS[
            operator_type
        ](
            left,
            right
        )

    # --------------------------------------------------------
    # Unary operation
    # --------------------------------------------------------

    if isinstance(
        node,
        ast.UnaryOp
    ):

        value = safe_calculate(
            node.operand
        )

        if isinstance(
            node.op,
            ast.USub
        ):

            return -value

        if isinstance(
            node.op,
            ast.UAdd
        ):

            return value

    raise ValueError(
        "Invalid expression"
    )


def calculate_expression(
    expression
):

    tree = ast.parse(
        expression,
        mode="eval"
    )

    return safe_calculate(
        tree
    )


def format_calculator_result(
    result
):

    if isinstance(
        result,
        float
    ):

        if not math.isfinite(
            result
        ):

            raise ValueError(
                "Invalid result"
            )

        if result.is_integer():

            return str(
                int(result)
            )

        return (
            f"{result:.10f}"
            .rstrip("0")
            .rstrip(".")
        )

    return str(result)


def calculator_command(command):

    expression = command.lower().strip()

    # ========================================================
    # Remove common phrases
    # ========================================================

    expression = expression.replace(
        "what is",
        ""
    )

    expression = expression.replace(
        "calculate",
        ""
    )

    expression = expression.replace(
        "please calculate",
        ""
    )

    expression = expression.strip()

    # ========================================================
    # SQUARE ROOT
    # ========================================================

    match = re.search(
        r"square root(?: of)?\s*(-?\d+(?:\.\d+)?)",
        expression
    )

    if match:

        try:

            number = float(
                match.group(1)
            )

            if number < 0:

                speak(
                    "I cannot calculate the square root "
                    "of a negative number."
                )

                return True

            result = math.sqrt(
                number
            )

            speak(
                f"The square root is {result:.4f}"
            )

            print(
                "Calculator result:",
                result
            )

            return True

        except Exception as e:

            print(
                "Square root error:",
                e
            )

            speak(
                "Sorry, I could not calculate the square root."
            )

            return True

    # ========================================================
    # CUBE ROOT
    # ========================================================

    match = re.search(
        r"cube root(?: of)?\s*(-?\d+(?:\.\d+)?)",
        expression
    )

    if match:

        try:

            number = float(
                match.group(1)
            )

            result = math.copysign(
                abs(number) ** (1 / 3),
                number
            )

            speak(
                f"The cube root is {result:.4f}"
            )

            print(
                "Calculator result:",
                result
            )

            return True

        except Exception as e:

            print(
                "Cube root error:",
                e
            )

            speak(
                "Sorry, I could not calculate the cube root."
            )

            return True

    # ========================================================
    # SQUARED
    # ========================================================

    match = re.search(
        r"(-?\d+(?:\.\d+)?)\s+squared",
        expression
    )

    if match:

        try:

            number = float(
                match.group(1)
            )

            result = number ** 2

            result_text = format_calculator_result(
                result
            )

            speak(
                f"The answer is {result_text}"
            )

            print(
                "Calculator result:",
                result_text
            )

            return True

        except Exception as e:

            print(
                "Squared calculation error:",
                e
            )

            speak(
                "Sorry, I could not calculate that."
            )

            return True

    # ========================================================
    # CUBED
    # ========================================================

    match = re.search(
        r"(-?\d+(?:\.\d+)?)\s+cubed",
        expression
    )

    if match:

        try:

            number = float(
                match.group(1)
            )

            result = number ** 3

            result_text = format_calculator_result(
                result
            )

            speak(
                f"The answer is {result_text}"
            )

            print(
                "Calculator result:",
                result_text
            )

            return True

        except Exception as e:

            print(
                "Cubed calculation error:",
                e
            )

            speak(
                "Sorry, I could not calculate that."
            )

            return True

    # ========================================================
    # SPOKEN OPERATORS
    # ========================================================

    replacements = {

        "multiplied by": "*",
        "multiply by": "*",

        "divided by": "/",
        "divide by": "/",
        "divided": "/",
        "divide": "/",

        "to the power of": "**",

        "plus": "+",
        "minus": "-",

        "times": "*",

        "modulo": "%",
        "mod": "%",

        "×": "*",

        # Spoken "x" multiplication
        " x ": "*"

    }

    # Replace longer phrases first
    for old, new in replacements.items():

        expression = expression.replace(
            old,
            new
        )

    # ========================================================
    # Clean expression
    # ========================================================

    expression = expression.replace(
        "equals",
        ""
    )

    expression = expression.replace(
        "equal to",
        ""
    )

    expression = expression.strip()

    # ========================================================
    # NORMAL CALCULATOR
    # ========================================================

    try:

        # Only mathematical characters are allowed
        if not re.fullmatch(
            r"[0-9+\-*/%.()\s]+",
            expression
        ):

            print(
                "Invalid calculator expression:",
                expression
            )

            return False

        if not expression:

            return False

        result = calculate_expression(
            expression
        )

        result_text = format_calculator_result(
            result
        )

        print()
        print(
            "Calculator:",
            expression,
            "=",
            result_text
        )

        speak(
            f"The answer is {result_text}"
        )

        return True

    except ZeroDivisionError:

        speak(
            "You cannot divide by zero."
        )

        return True

    except OverflowError:

        speak(
            "The result is too large to calculate."
        )

        return True

    except Exception as e:

        print(
            "Calculator error:",
            e
        )

        return False


# ============================================================
# GOOGLE SEARCH
# ============================================================

def google_search(command):

    if command.startswith(
        "search "
    ):

        query = command[
            len("search "):
        ].strip()

    else:

        query = ""

    if not query:

        query = listen_with_retry(
            "What should I search for?"
        )

    if not query:
        return True

    url = (
        "https://www.google.com/search?q="
        + urllib.parse.quote(query)
    )

    webbrowser.open(
        url
    )

    speak(
        f"Searching Google for {query}"
    )

    pause_assistant_for_enter()

    return True


# ============================================================
# YOUTUBE
# ============================================================

def youtube_command(command):

    if command in [
        "youtube",
        "open youtube"
    ]:

        webbrowser.open(
            "https://www.youtube.com"
        )

        speak(
            "Opening YouTube."
        )

        pause_assistant_for_enter()

        return True

    query = ""

    if command.startswith(
        "play "
    ):

        query = command[
            len("play "):
        ].strip()

    elif command.startswith(
        "search youtube "
    ):

        query = command[
            len("search youtube "):
        ].strip()

    elif command.startswith(
        "youtube "
    ):

        query = command[
            len("youtube "):
        ].strip()

    if not query:
        return False

    url = (
        "https://www.youtube.com/results?search_query="
        + urllib.parse.quote(query)
    )

    webbrowser.open(
        url
    )

    speak(
        f"Searching YouTube for {query}"
    )

    pause_assistant_for_enter()

    return True


# ============================================================
# WEBSITES
# ============================================================

WEBSITES = {

    "open google":
        "https://www.google.com",

    "open youtube":
        "https://www.youtube.com",

    "open facebook":
        "https://www.facebook.com",

    "open instagram":
        "https://www.instagram.com",

    "open gmail":
        "https://mail.google.com",

    "open github":
        "https://github.com",

    "open chatgpt":
        "https://chatgpt.com"

}


def website_command(command):

    if command not in WEBSITES:
        return False

    webbrowser.open(
        WEBSITES[command]
    )

    name = command.replace(
        "open ",
        ""
    )

    speak(
        f"Opening {name}."
    )

    pause_assistant_for_enter()

    return True


# ============================================================
# WINDOWS APPLICATIONS
# ============================================================

def app_command(command):

    apps = {

        "open notepad":
            ("notepad.exe", "Notepad"),

        "notepad":
            ("notepad.exe", "Notepad"),

        "open calculator":
            ("calc.exe", "Calculator"),

        "calculator":
            ("calc.exe", "Calculator"),

        "open calc":
            ("calc.exe", "Calculator"),

        "open command prompt":
            ("cmd.exe", "Command Prompt"),

        "open cmd":
            ("cmd.exe", "Command Prompt"),

        "command prompt":
            ("cmd.exe", "Command Prompt"),

        "open file explorer":
            ("explorer.exe", "File Explorer"),

        "open explorer":
            ("explorer.exe", "File Explorer"),

        "file explorer":
            ("explorer.exe", "File Explorer")

    }

    if command not in apps:
        return False

    executable, name = apps[
        command
    ]

    try:

        subprocess.Popen(
            executable
        )

        speak(
            f"Opening {name}."
        )

        pause_assistant_for_enter()

        return True

    except Exception as e:

        print(
            "Application error:",
            e
        )

        speak(
            f"Sorry, I could not open {name}."
        )

        return True


# ============================================================
# WINDOWS FOLDERS
# ============================================================

def folder_command(command):

    home = os.path.expanduser(
        "~"
    )

    folders = {

        "open desktop":
            os.path.join(
                home,
                "Desktop"
            ),

        "open downloads":
            os.path.join(
                home,
                "Downloads"
            ),

        "open documents":
            os.path.join(
                home,
                "Documents"
            ),

        "open pictures":
            os.path.join(
                home,
                "Pictures"
            ),

        "open videos":
            os.path.join(
                home,
                "Videos"
            ),

        "open music":
            os.path.join(
                home,
                "Music"
            ),

        "open home":
            home

    }

    if command not in folders:
        return False

    path = folders[
        command
    ]

    if not os.path.exists(path):

        speak(
            "That folder does not exist."
        )

        return True

    try:

        os.startfile(
            path
        )

        speak(
            "Opening folder."
        )

        pause_assistant_for_enter()

    except Exception as e:

        print(
            "Folder error:",
            e
        )

        speak(
            "Sorry, I could not open the folder."
        )

    return True


# ============================================================
# VOLUME
# ============================================================

def volume_up():

    try:

        subprocess.run(
            [
                "powershell",
                "-Command",
                "(New-Object -ComObject "
                "WScript.Shell).SendKeys([char]175)"
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False
        )

        speak(
            "Volume increased."
        )

    except Exception as e:

        print(
            "Volume error:",
            e
        )


def volume_down():

    try:

        subprocess.run(
            [
                "powershell",
                "-Command",
                "(New-Object -ComObject "
                "WScript.Shell).SendKeys([char]174)"
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False
        )

        speak(
            "Volume decreased."
        )

    except Exception as e:

        print(
            "Volume error:",
            e
        )


def volume_mute():

    try:

        subprocess.run(
            [
                "powershell",
                "-Command",
                "(New-Object -ComObject "
                "WScript.Shell).SendKeys([char]173)"
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False
        )

        speak(
            "Mute toggled."
        )

    except Exception as e:

        print(
            "Mute error:",
            e
        )


# ============================================================
# SYSTEM COMMANDS
# ============================================================

def system_command(command):

    if command in [
        "lock computer",
        "lock pc",
        "lock system"
    ]:

        speak(
            "Locking the computer."
        )

        ctypes.windll.user32.LockWorkStation()

        return True

    if command in [
        "shutdown",
        "shutdown computer",
        "shutdown pc"
    ]:

        speak(
            "Shutting down the computer."
        )

        subprocess.Popen(
            [
                "shutdown",
                "/s",
                "/t",
                "0"
            ]
        )

        return True

    if command in [
        "restart",
        "restart computer",
        "restart pc"
    ]:

        speak(
            "Restarting the computer."
        )

        subprocess.Popen(
            [
                "shutdown",
                "/r",
                "/t",
                "0"
            ]
        )

        return True

    if command in [
        "cancel shutdown",
        "abort shutdown"
    ]:

        subprocess.Popen(
            [
                "shutdown",
                "/a"
            ]
        )

        speak(
            "Shutdown cancelled."
        )

        return True

    if command in [
        "volume up",
        "increase volume",
        "increase the volume"
    ]:

        volume_up()

        return True

    if command in [
        "volume down",
        "decrease volume",
        "decrease the volume"
    ]:

        volume_down()

        return True

    if command in [
        "mute",
        "mute volume",
        "unmute"
    ]:

        volume_mute()

        return True

    return False


# ============================================================
# PAUSE ASSISTANT UNTIL ENTER
# ============================================================

def pause_assistant_for_enter():

    global assistant_paused

    assistant_paused = True

    print()
    print(
        "================================"
    )
    print(
        "ASSISTANT PAUSED"
    )
    print(
        "Microphone is OFF."
    )
    print(
        "Press ENTER to continue."
    )
    print(
        "================================"
    )

    try:

        input()

    except Exception:

        pass

    assistant_paused = False

    print(
        "Assistant resumed."
    )


# ============================================================
# REMINDER TIMER
# ============================================================

def reminder_timer(
    seconds,
    reminder_text
):

    global assistant_paused
    global reminder_active
    global reminder_message

    try:

        time.sleep(
            seconds
        )

        # ----------------------------------------------------
        # Reminder starts
        # ----------------------------------------------------

        assistant_paused = True

        reminder_active = True

        reminder_message = reminder_text

        print()
        print(
            "================================"
        )
        print(
            "REMINDER!"
        )
        print(
            reminder_text
        )
        print(
            "================================"
        )

        speak(
            f"Reminder. {reminder_text}"
        )

    except Exception as e:

        print(
            "Reminder timer error:",
            e
        )

    finally:

        reminder_active = False

        reminder_message = ""

        assistant_paused = False

        print(
            "Reminder finished."
        )

        print(
            "Assistant resumed listening."
        )


# ============================================================
# REMINDER COMMAND
# ============================================================

def reminder_command(command):

    match = re.search(
        r"remind me in\s+"
        r"(\d+)\s*"
        r"(second|seconds|minute|minutes|hour|hours)",
        command
    )

    if not match:
        return False

    amount = int(
        match.group(1)
    )

    unit = match.group(2)

    if "second" in unit:

        seconds = amount

        time_text = (
            f"{amount} seconds"
        )

    elif "minute" in unit:

        seconds = amount * 60

        time_text = (
            f"{amount} minutes"
        )

    else:

        seconds = amount * 3600

        time_text = (
            f"{amount} hours"
        )

    text_match = re.search(
        r"\bto\s+(.+)$",
        command
    )

    reminder_text = ""

    if text_match:

        reminder_text = text_match.group(
            1
        ).strip()

    if not reminder_text:

        reminder_text = listen_with_retry(
            "What should I remind you about?"
        )

    if not reminder_text:

        speak(
            "Reminder cancelled."
        )

        return True

    global assistant_paused
    global reminder_active
    global reminder_message

    reminder_active = True

    reminder_message = reminder_text

    # Pause immediately
    assistant_paused = True

    print()

    print(
        f"Reminder set for {time_text}."
    )

    speak(
        f"Reminder set for {time_text}."
    )

    threading.Thread(
        target=reminder_timer,
        args=(
            seconds,
            reminder_text
        ),
        daemon=True
    ).start()

    return True


# ============================================================
# CUSTOM COMMANDS JSON
# ============================================================

def load_custom_commands():

    file_path = os.path.join(
        os.path.dirname(
            os.path.abspath(__file__)
        ),
        CUSTOM_COMMANDS_FILE
    )

    if not os.path.exists(
        file_path
    ):

        return []

    try:

        with open(
            file_path,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(
                file
            )

        if not isinstance(
            data,
            dict
        ):

            return []

        return data.get(
            "commands",
            []
        )

    except Exception as e:

        print(
            "Custom commands error:",
            e
        )

        return []


def run_custom_command(command):

    commands = load_custom_commands()

    for item in commands:

        phrases = [

            str(phrase).lower().strip()

            for phrase in item.get(
                "phrases",
                []
            )

        ]

        if command not in phrases:
            continue

        action = item.get(
            "action",
            ""
        )

        value = item.get(
            "value",
            ""
        )

        name = item.get(
            "name",
            "custom command"
        )

        # ----------------------------------------------------
        # OPEN URL
        # ----------------------------------------------------

        if (
            action == "open_url"
            and isinstance(
                value,
                str
            )
            and value.startswith(
                (
                    "https://",
                    "http://"
                )
            )
        ):

            webbrowser.open(
                value
            )

            speak(
                f"Opening {name}."
            )

            pause_assistant_for_enter()

            return True

        # ----------------------------------------------------
        # SPEAK
        # ----------------------------------------------------

        if action == "speak":

            speak(
                value
            )

            return True

        # ----------------------------------------------------
        # OPEN FOLDER
        # ----------------------------------------------------

        if action == "open_folder":

            if os.path.isdir(
                value
            ):

                os.startfile(
                    value
                )

                speak(
                    f"Opening {name}."
                )

                pause_assistant_for_enter()

                return True

            speak(
                "That folder does not exist."
            )

            return True

        print(
            "Unsupported custom command:",
            action
        )

        return True

    return False


# ============================================================
# PROCESS COMMAND
# ============================================================

def process_command(command):

    command = command.lower().strip()

    if not command:
        return None

    print()
    print(
        "Processing command:",
        command
    )

    # ========================================================
    # EXIT
    # ========================================================

    if command in [

        "exit",
        "quit",
        "stop",
        "close assistant",
        "shutdown assistant",
        "goodbye"

    ]:

        speak(
            "Goodbye. Assistant is shutting down."
        )

        return "exit"

    # ========================================================
    # CUSTOM JSON COMMAND
    # ========================================================

    if run_custom_command(
        command
    ):

        return True

    # ========================================================
    # INTENT
    # ========================================================

    intent = detect_intent(
        command
    )

    print(
        "Detected intent:",
        intent
    )

    # ========================================================
    # GREETING
    # ========================================================

    if intent == "greeting":

        if greeting_command(
            command
        ):

            return True

    # ========================================================
    # TIME
    # ========================================================

    if intent == "time":

        time_command()

        return True

    # ========================================================
    # DATE
    # ========================================================

    if intent == "date":

        date_command()

        return True

    # ========================================================
    # WEATHER
    # ========================================================

    if intent == "weather":

        return weather_command(
            command
        )

    # ========================================================
    # NEWS
    # ========================================================

    if intent == "news":

        return news_command(
            command
        )

    # ========================================================
    # EMAIL
    # ========================================================

    if intent == "email":

        return email_command(
            command
        )

    # ========================================================
    # REMINDER
    # ========================================================

    if intent == "reminder":

        return reminder_command(
            command
        )

    # ========================================================
    # CALCULATOR
    # ========================================================

    if intent == "calculator":

        if calculator_command(
            command
        ):

            return True

    # ========================================================
    # GOOGLE SEARCH
    # ========================================================

    if command.startswith(
        "search "
    ):

        return google_search(
            command
        )

    # ========================================================
    # YOUTUBE
    # ========================================================

    if intent == "youtube":

        if youtube_command(
            command
        ):

            return True

    # ========================================================
    # WEBSITE
    # ========================================================

    if website_command(
        command
    ):

        return True

    # ========================================================
    # WINDOWS APP
    # ========================================================

    if app_command(
        command
    ):

        return True

    # ========================================================
    # FOLDER
    # ========================================================

    if folder_command(
        command
    ):

        return True

    # ========================================================
    # SYSTEM
    # ========================================================

    if system_command(
        command
    ):

        return True

    # ========================================================
    # AI
    # ========================================================

    if intent == "ai":

        if ai_command(
            command
        ):

            return True

    # ========================================================
    # GENERAL KNOWLEDGE
    # ========================================================

    if intent == "general_knowledge":

        return general_knowledge_command(
            command
        )

    # ========================================================
    # UNKNOWN
    # ========================================================

    speak(
        "I heard you, but I don't know that command yet."
    )

    return False


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print(
        "========================================"
    )
    print(
        "          MY VOICE ASSISTANT"
    )
    print(
        "========================================"
    )

    print()

    print(
        "Wake Word:",
        WAKE_WORD
    )

    print(
        "Microphone Index:",
        MIC_INDEX
    )

    print()

    speak(
        "Voice assistant started."
    )

    speak(
        "Say Hey Assistant to start."
    )

    # --------------------------------------------------------
    # Wake word
    # --------------------------------------------------------

    wake_command = wait_for_wake_word()

    if not wake_command:

        speak(
            "Could not activate assistant."
        )

        return

    # --------------------------------------------------------
    # Remove wake word
    # --------------------------------------------------------

    remaining_command = wake_command.replace(
        WAKE_WORD,
        "",
        1
    ).strip()

    speak(
        "Yes, I am ready."
    )

    # --------------------------------------------------------
    # If command was spoken with wake word
    #
    # Example:
    # Hey Assistant open Google
    # --------------------------------------------------------

    if remaining_command:

        result = process_command(
            remaining_command
        )

        if result == "exit":

            return

    else:

        speak(
            "How can I help you?"
        )

    # --------------------------------------------------------
    # MAIN LOOP
    # --------------------------------------------------------

    while True:

        # ----------------------------------------------------
        # Reminder / pause
        # ----------------------------------------------------

        if assistant_paused:

            time.sleep(
                0.5
            )

            continue

        command = listen()

        if not command:

            continue

        result = process_command(
            command
        )

        if result == "exit":

            print()

            print(
                "========================================"
            )

            print(
                "Assistant stopped."
            )

            print(
                "========================================"
            )

            break


# ============================================================
# START PROGRAM
# ============================================================

if __name__ == "__main__":

    try:

        main()

    except KeyboardInterrupt:

        print()

        print(
            "Assistant stopped by user."
        )

    except Exception as e:

        print()

        print(
            "Fatal error:",
            e
        )