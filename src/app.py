import signal
import sys
from flask import Flask, render_template, jsonify, Response
from flask_cors import CORS
import threading
import serial
from speechRecognition import record_audio, recognize_speech
from voiceOut import Voice_out
from generativeai import get_response
from actions import Action_Detection
from emotions import Face_Emotion_Recognition
from message import user_message_queue, bot_message_queue, send_user_message, send_bot_message

app = Flask(__name__)
CORS(app)
current_mode_thread = None

# Initialize Serial Communication
arduino = serial.Serial('COM3', 9600)  # Change COM3 to the correct port for your Arduino

Voice_out('Hi, Welcome, I am Samartha, the smart A I Robot', arduino)

# Function to control Arduino LEDs
def control_led(mode):
    arduino.write((mode + "\n").encode())

# Function to run action mode
def run_action_mode():
    control_led("action_mode")
    Action_Detection(arduino)

# Function to run chat mode
def run_chat_mode():
    chat_thread = threading.current_thread()
    control_led("chat_mode")
    while getattr(chat_thread, "do_run", True):
        control_led("emotion_mode")
        Face_Emotion_Recognition(arduino)
        while getattr(chat_thread, "do_run", True):
            audio = record_audio()
            text = recognize_speech(audio)
            print('Recognized text:', text)
            if text:
                send_user_message(text)
            if text.lower() in ["hello","hello tasa", "hello tesa", "hello tessa", "hey tessa", "tesa", "tasa", "hatasha", "hello tesla", "tesla", "hi tessa", "hi chacha","hello chacha"]:
                break
            elif text.lower() == "":
                continue
            else:
                response = get_response(text)
                send_bot_message(response)
                Voice_out(response, arduino)
                control_led("chat_mode")
        Voice_out('Hi', arduino)
        audio = record_audio()
        text = recognize_speech(audio)
        if text.lower() == "stop chat" or text.lower() == "stop":
            break
    return 'ended'



@app.route('/get_messages', methods=["GET"])
def get_messages():
    user_messages = []
    bot_messages = []
    
    # Get and clear the messages from the queues
    while user_message_queue:
        user_messages.append(user_message_queue.pop(0))
    while bot_message_queue:
        bot_messages.append(bot_message_queue.pop(0))

    return jsonify({
        'userMessages': user_messages,
        'botMessages': bot_messages
    })



@app.route('/')
def index():
    global current_mode_thread
    if current_mode_thread and current_mode_thread.is_alive():
        current_mode_thread.do_run = False
        current_mode_thread.join()
        Voice_out("Stopping the current mode.", arduino)
    return render_template('index.html')

@app.route('/activate', methods=["POST", "GET"])
def activate():
    control_led("activated")
    global current_mode_thread
    if current_mode_thread and current_mode_thread.is_alive():
        current_mode_thread.do_run = False
        current_mode_thread.join()
    Voice_out("Hello, what can I do for you?", arduino)
    return jsonify({'message': 'Activated!'})

@app.route('/stop')
def stop():
    control_led("off")
    global current_mode_thread
    if current_mode_thread and current_mode_thread.is_alive():
        current_mode_thread.do_run = False
        current_mode_thread.join()
    Voice_out("Stopping the current mode.", arduino)
    return render_template('index.html')

@app.route('/action_mode', methods=["GET"])
def action_mode():
    global current_mode_thread
    if current_mode_thread and current_mode_thread.is_alive():
        current_mode_thread.do_run = False
        current_mode_thread.join()
    Voice_out("Action Mode Activated.", arduino)
    control_led("stop_mode")
    current_mode_thread = threading.Thread(target=run_action_mode)
    current_mode_thread.start()
    return jsonify({'message': 'Activated!'})

@app.route('/chat_mode', methods=["GET"])
def chat_mode():
    global current_mode_thread
    if current_mode_thread and current_mode_thread.is_alive():
        current_mode_thread.do_run = False
        current_mode_thread.join()
    Voice_out("Chat Mode Activated.", arduino)
    control_led("stop_mode")
    current_mode_thread = threading.Thread(target=run_chat_mode)
    current_mode_thread.start()
    return jsonify({'message': 'Activated!'})

if __name__ == '__main__':
    app.run(debug=False, threaded=True)
