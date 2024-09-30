import pyttsx3

def control_led(mode, arduino):
    arduino.write((mode + "\n").encode())

def Voice_out(message, arduino):
    control_led('voice', arduino)
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')
    rate = engine.getProperty('rate')
    engine.setProperty('rate', 145)
    engine.setProperty('voice', voices[1].id)
    engine.say(message)
    engine.runAndWait()