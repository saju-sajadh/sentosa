import os
import threading
import serial
from speechRecognition import record_audio, recognize_speech
from voiceOut import Voice_out
from generativeai import get_response
from face import Face_Recog
from emotions import EmotionDetector
from src.actions import Action_Detection
from faceEmotions import Face_Emotion_Recognition

# Initialize Serial Communication
arduino = serial.Serial('COM4', 9600)  # Change COM4 to the correct port for your Arduino

# Function to control Arduino LEDs
def control_led(mode):
    arduino.write((mode + "\n").encode())

# Function to run face recognition
def run_face_recognition():
    control_led("face_mode")
    Face_Recog()

# Function to run emotion detection
def run_emotion_detection():
    control_led("emotion_mode")
    # emotion = EmotionDetector()
    # emotion.detect_emotion(arduino)
    Face_Emotion_Recognition(arduino)
    

def run_action_mode():
    control_led("action_mode")
    Action_Detection(arduino)

def run_chat_mode():
    # control_led("chat_mode")
    Voice_out("Chat mode activated! How can I assist you?",  arduino)
    control_led("chat_mode")
    while True:
        audio = record_audio()
        text = recognize_speech(audio)
        if text.lower() == "stop chat mode":
            Voice_out("Stopping chat mode.", arduino)
            break
        elif text.lower() == "":
            continue
        else:
            response = get_response(text)
            Voice_out(response,  arduino)
            control_led("chat_mode")
    return 'ended'

# Define the main function
def main():

    current_mode_thread = None
    control_led("off")  # Turn off the LED initially
    Voice_out('Hai, Welcome to nermala bavan school..... I am Tessa, an A.I powered robot specially designed for schools with advanced facial recognition and emotion detection . I interact with people, monitor students, and help maintain discipline by keeping an eye on fights and behavior. Lets work together to create a safer and harmonious environment', arduino)
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
                elif text.lower() == "activate action mode" or text.lower() == "activate action"  or  text.lower() == "action mode" or text.lower() == "activity action mode":
                    Voice_out("Action mode is activated!. This mode is for monitoring and analyzing students behavior.", arduino)
                    if current_mode_thread and current_mode_thread.is_alive():
                        current_mode_thread.do_run = False
                        current_mode_thread.join()
                    current_mode_thread = threading.Thread(target=run_action_mode)
                    current_mode_thread.start()
                elif text.lower() == "activate face mode" or text.lower() == "activate safe mode" or text.lower() == "safe mode" or  text.lower() == "face mode":
                    Voice_out("Face mode activated!. This mode is for recognizing and identifying individuals, enabling advanced people recognition capabilities.", arduino)
                    if current_mode_thread and current_mode_thread.is_alive():
                        current_mode_thread.do_run = False
                        current_mode_thread.join()
                    current_mode_thread = threading.Thread(target=run_face_recognition)
                    current_mode_thread.start()
                elif text.lower() == "activate emotion mode" or text.lower() == "activate motion mode" or text.lower() == "motion mode" or text.lower() == "emotion mode":
                    Voice_out("Emotion mode activated!. This mode is for detecting and analyzing your facial expressions and emotions.", arduino)
                    if current_mode_thread and current_mode_thread.is_alive():
                        current_mode_thread.do_run = False
                        current_mode_thread.join()
                    current_mode_thread = threading.Thread(target=run_emotion_detection)
                    current_mode_thread.start()
                elif text.lower() == "activate chat mode" or text.lower() == "chat mode" or text.lower() == "activate chat":
                    if current_mode_thread and current_mode_thread.is_alive():
                        current_mode_thread.do_run = False
                        current_mode_thread.join()
                    next_mode = run_chat_mode()
                    if next_mode.lower() == "stop chat mode":
                        Voice_out("Chat mode ended. What would you like to do next?", arduino)
                        control_led("stop_mode")
                    
        else:
            print("Not activated.")
            control_led("off")  # Turn off the LED if the program is not activated

if __name__ == "__main__":
    main()