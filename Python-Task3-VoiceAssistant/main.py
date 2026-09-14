import speech_recognition as sr
import pyttsx3
import datetime
import webbrowser

# Initialize text-to-speech engine
engine = pyttsx3.init()

# Set voice properties (optional)
engine.setProperty('rate', 170)

def speak(text):
    print("Assistant:", text)
    engine.say(text)
    engine.runAndWait()

def listen():
    recognizer = sr.Recognizer()

    try:
        with sr.Microphone() as source:

            print("\nListening...")
            recognizer.adjust_for_ambient_noise(source, duration=1)

            audio = recognizer.listen(
                source,
                timeout=5,
                phrase_time_limit=5
            )

            print("Recognizing...")

            command = recognizer.recognize_google(audio)

            print("You:", command)

            return command.lower()

    except sr.WaitTimeoutError:
        speak("No speech detected.")
        return ""

    except sr.UnknownValueError:
        speak("Sorry, I could not understand. Please repeat.")
        return ""

    except sr.RequestError:
        speak("Network error. Please check your internet connection.")
        return ""

    except Exception as e:
        print("Error:", e)
        speak("Microphone error occurred.")
        return ""

def tell_time():
    current_time = datetime.datetime.now().strftime("%I:%M %p")
    speak(f"The current time is {current_time}")

def tell_date():
    current_date = datetime.datetime.now().strftime("%d %B %Y")
    speak(f"Today's date is {current_date}")

def search_web(query):

    if query.strip() == "":
        speak("Please tell me what to search.")
        return

    url = f"https://www.google.com/search?q={query}"

    webbrowser.open(url)

    speak(f"Searching for {query}")

def main():

    speak("Hello. I am your voice assistant.")

    while True:

        command = listen()

        if command == "":
            continue

        elif "hello" in command:
            speak("Hello, how can I help you?")

        elif "time" in command:
            tell_time()

        elif "date" in command:
            tell_date()

        elif "search" in command:

            query = command.replace("search", "").strip()

            if query == "":
                speak("What would you like me to search?")
            else:
                search_web(query)

        elif "exit" in command or "stop" in command or "bye" in command:
            speak("Goodbye. Have a nice day.")
            break

        else:
            speak("Sorry, I do not know that command.")

if __name__ == "__main__":
    main()