
import speech_recognition as sr
import audioop

recognizer = sr.Recognizer()

# Test your Airdopes microphone first
MIC_INDEX = 2

print("====================================")
print("      MICROPHONE AUDIO TEST")
print("====================================")

try:
    with sr.Microphone(device_index=MIC_INDEX) as source:

        print("\nMicrophone connected.")
        print("Stay quiet for 2 seconds...")
        recognizer.adjust_for_ambient_noise(source, duration=2)

        print("\nNow speak loudly for 5 seconds.")
        print("Say: Hello, this is a microphone test.")

        audio = recognizer.listen(
            source,
            timeout=10,
            phrase_time_limit=5
        )

    # Calculate audio volume
    raw_audio = audio.get_raw_data()
    volume = audioop.rms(raw_audio, 2)

    print("\n====================================")
    print("AUDIO TEST RESULT")
    print("====================================")
    print("Audio volume:", volume)

    if volume < 100:
        print("\nPROBLEM:")
        print("Python is receiving very weak audio.")
        print("Check Windows microphone/input settings.")

    elif volume < 500:
        print("\nAudio is detected, but it is quite weak.")

    else:
        print("\nGOOD!")
        print("Python is receiving your voice clearly.")

except Exception as e:
    print("\nERROR:")
    print(type(e).__name__)
    print(str(e))

