import os
import threading
import serial
from speechRecognition import record_audio, recognize_speech
from voiceOut import Voice_out
from generativeai import get_response
from actions import Action_Detection
from  commands import action_modes, chat_modes
from emotions import Face_Emotion_Recognition

# Initialize Serial Communication
arduino = serial.Serial('COM4', 9600)  # Change COM4 to the correct port for your Arduino

# Function to control Arduino LEDs
def control_led(mode):
    arduino.write((mode + "\n").encode())
    

def run_action_mode():
    control_led("action_mode")
    Action_Detection(arduino)

def run_chat_mode():
    control_led("chat_mode")
    while True:
        control_led("emotion_mode")
        Face_Emotion_Recognition(arduino)
        while True:
            audio = record_audio()
            text = recognize_speech(audio)
            print('text', text)
            if text.lower() == "hello" or text.lower() == "hello tesa" or text.lower() == "hey tesa" or text.lower() == "hello tesla" or text.lower() == "tesa" or  text.lower() == "tasa" or  text.lower() == "hatasha":
                break
            elif text.lower() == "":
                continue
            else:
                response = get_response(text)
                Voice_out(response,  arduino)
                control_led("chat_mode")
        Voice_out('Hi', arduino)
        audio = record_audio()
        text = recognize_speech(audio)
        if text.lower() == "stop chat" or text.lower() == "stop":
            break
    return 'ended'
# Define the main function
def main():

    current_mode_thread = None
    control_led("off")  # Turn off the LED initially
    Voice_out('Hai, Welcome , I am Tessa', arduino)
    while True:
        audio = record_audio()
        text = recognize_speech(audio)
        if text.lower() == "hello" or text.lower() == "hello tesa" or text.lower() == "hello tasa" or text.lower() == "hello tesla" or text.lower() == "tesa" or  text.lower() == "tasa" or text.lower() == "activate chat mode" or text.lower() == "tesla":
            print("Activated!")
              # Light up a color when the program is activated
            Voice_out("Hello, what can I do for you?", arduino)
            control_led("activated")
            while True:
                audio = record_audio()
                text = recognize_speech(audio)
                if text.lower() == "stop":
                    if current_mode_thread and current_mode_thread.is_alive():
                        Voice_out("Stopping the current mode.", arduino)
                        control_led("stop_mode")
                        current_mode_thread.do_run = False
                        current_mode_thread.join()
                    control_led("off")  # Turn off the LED when the program is stopped
                    break
                elif text.lower() in action_modes:
                    Voice_out("Action mode is activated!. This mode is for monitoring and analyzing students behavior.", arduino)
                    if current_mode_thread and current_mode_thread.is_alive():
                        current_mode_thread.do_run = False
                        current_mode_thread.join()
                    current_mode_thread = threading.Thread(target=run_action_mode)
                    current_mode_thread.start()
                elif text.lower() in chat_modes:
                    if current_mode_thread and current_mode_thread.is_alive():
                        current_mode_thread.do_run = False
                        current_mode_thread.join()
                    next_mode = run_chat_mode()
                    if next_mode.lower() == "ended":
                        Voice_out("Chat mode ended. What would you like to do next?", arduino)
                        control_led("stop_mode")
                    
        else:
            print("Not activated.")
            control_led("off")  # Turn off the LED if the program is not activated

if __name__ == "__main__":
    main()