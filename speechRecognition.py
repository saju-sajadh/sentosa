import speech_recognition as sr




recognizer = sr.Recognizer()

def record_audio():
    with sr.Microphone() as source:
        print('Listening....')
        audio = recognizer.listen(source, 10, 3)
        print('recorded...')
    return audio

def recognize_speech(audio):
    try:
        print('processing speech...')
        text = recognizer.recognize_google(audio)
        print(f"You said: {text}")
        return text
    except sr.UnknownValueError:
        return "Sorry, I couldn't understand that."
    except sr.RequestError:
        return "Sorry, there was an error processing your request."