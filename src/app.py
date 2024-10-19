from flask import Flask, render_template, jsonify, request, Response
from flask_cors import CORS
import multiprocessing
import serial
import time
from speechRecognition import record_audio_process
from voiceOut import Voice_out
from generativeai import get_response
from message import send_user_message, send_bot_message  # Import only the functions
from multiprocessing import Queue, Lock, Manager, Value
from threadOne import face_recognition_process
import logging



app = Flask(__name__)
CORS(app)
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

audio_queue = Queue()
face_process = None
audio_process = None
face_position = {'x': 0, 'y': 0}


class FakeArduino:
    def write(self, data):
        print(f"FakeArduino received: {data}")

    def close(self):
        print("FakeArduino connection closed")

try:
    arduino = serial.Serial('COM3', 9600)
    print("Connected to Arduino")
except serial.SerialException:
    arduino = FakeArduino()
    print("No Arduino found, using FakeArduino")

# Voice_out('Hi, Welcome, I am Samartha, the smart A I Robot', arduino)

# Function to control Arduino LEDs
def control_led(mode):
    arduino.write((mode + "\n").encode())

# Function to run chat mode in a separate process
def run_chat_mode(audio_queue, user_message_queue, bot_message_queue, is_listening, lock):
    control_led("chat_mode")
    while True:
        # Record and process audio
        text = record_audio_process(audio_queue, is_listening, lock)
        print('Recognized text:', text)

        if text:
            send_user_message(text, user_message_queue)  # Pass the shared queue
            response = get_response(text)
            send_bot_message(response, bot_message_queue)  # Pass the shared queue
            if response.startswith("111"):
                response = response[3:]
            Voice_out(response, arduino)
            control_led("chat_mode")
        elif text.lower() == "":
            continue
        else:
            continue


@app.route('/update_position', methods=['POST'])
def update_position():
    global face_position
    data = request.get_json()
    face_position['x'] = data.get('x', 0)
    face_position['y'] = data.get('y', 0)
    return jsonify(success=True)

# Route to send position data to the frontend
@app.route('/get_position', methods=['GET'])
def get_position():
    return jsonify(face_position)

# Function to get messages for chat UI
@app.route('/get_messages', methods=["GET"])
def get_messages():
    user_messages = []
    bot_messages = []

    while not user_message_queue.empty():
        user_messages.append(user_message_queue.get())
        
    while not bot_message_queue.empty():
        bot_messages.append(bot_message_queue.get())

    return jsonify({
        'userMessages': user_messages,
        'botMessages': bot_messages
    })

@app.route('/listen_status')
def listen_status():
    def listen():
        try:
            while True:
                time.sleep(1)
                with lock:
                    status = "listening" if is_listening.value else "not listening"
                yield f"data: {status}\n\n"
        except GeneratorExit:
            print("SSE client disconnected")
        except Exception as e:
            print(f"Error in SSE: {e}")
    return Response(listen(), mimetype='text/event-stream')


@app.route('/')
def index():
    return render_template('index.html')

# Stop all running processes
@app.route('/stop', methods=["GET"])
def stop():
    global face_process, audio_process
    control_led("off")

    if audio_process:
        audio_process.terminate()
        audio_process.join()

    
    return jsonify({'message': 'started face registering!'})


# Activate chat mode (starts audio recognition process)
@app.route('/activate', methods=["GET"])
def chat_mode():
    global audio_process
    if audio_process:
        audio_process.terminate()
        audio_process.join()

    control_led("chat_mode")
    
    # Start a new process for chat mode
    audio_process = multiprocessing.Process(target=run_chat_mode, args=(audio_queue, user_message_queue, bot_message_queue, is_listening, lock))
    audio_process.start()

    return jsonify({'message': 'Activated!'})

# Run the app and face recognition process
if __name__ == '__main__':
    # Initialize Manager for shared queues
    manager = Manager()
    user_message_queue = manager.Queue()
    bot_message_queue = manager.Queue()
    is_listening = Value('b', False)  # 'b' for boolean
    lock = Lock()
    face_process = multiprocessing.Process(target=face_recognition_process, args=(arduino, user_message_queue, bot_message_queue))
    face_process.start()

    app.run(debug=False, threaded=True)
