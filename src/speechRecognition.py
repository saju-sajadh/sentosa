import speech_recognition as sr

recognizer = sr.Recognizer()

def record_audio_process(audio_queue, is_listening, lock):
    try:
        with sr.Microphone() as source:
            print('Listening....')
            with lock:
                is_listening.value = True
            audio = recognizer.listen(source, timeout=15, phrase_time_limit=10)  # Increased timeout and phrase time limit
            print('Recorded...')
            with lock:  
                is_listening.value = False
            text = recognizer.recognize_google(audio)
            audio_queue.put(text)
            return text
    except sr.UnknownValueError:
        audio_queue.put("")
        return ""
    except sr.RequestError:
        audio_queue.put("Sorry, there was an error processing your request.")
        return "Sorry, there was an error processing your request."
