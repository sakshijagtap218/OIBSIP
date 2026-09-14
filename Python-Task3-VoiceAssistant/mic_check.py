
import speech_recognition as sr

recognizer = sr.Recognizer()

# Use your working microphone
MIC_INDEX = 2

print("====================================")
print("   VOICE RECOGNITION TEST")
print("====================================")

try:
    with sr.Microphone(device_index=MIC_INDEX) as source:

        print("\nMicrophone connected.")

        print("Adjusting for background noise...")
        recognizer.adjust_for_ambient_noise(source, duration=2)

        # Make recognition more sensitive
        recognizer.energy_threshold = 300
        recognizer.dynamic_energy_threshold = True
        recognizer.pause_threshold = 0.8
        recognizer.phrase_threshold = 0.2
        recognizer.non_speaking_duration = 0.5

        print("\nSPEAK NOW")
        print("Say: Hello, how are you?")
        print("Listening...")

        audio = recognizer.listen(
            source,
            timeout=10,
            phrase_time_limit=6
        )

    print("\nAudio captured successfully!")
    print("Sending audio to Google...")
    print("Please wait...")

    text = recognizer.recognize_google(
        audio,
        language="en-IN"
    )

    print("\n====================================")
    print("SUCCESS!")
    print("You said:", text)
    print("====================================")

except sr.WaitTimeoutError:
    print("\nERROR: You did not speak within the time limit.")

except sr.UnknownValueError:
    print("\nERROR: Google could not understand the audio.")
    print("The microphone is working, but speech recognition failed.")

except sr.RequestError as e:
    print("\nERROR: Google speech service could not be reached.")
    print(e)

except Exception as e:
    print("\nERROR:", type(e).__name__)
    print(e)

