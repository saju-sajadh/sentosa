import numpy as np
import cv2
import threading
import tensorflow as tf
import face_recognition
import os
import math
import time
# Assuming this function outputs audio based on the input text
from emotionVoice import Voice_out
# Assuming this function generates a response text
from generativeai import get_response
import sys
from cameraindex import find_working_camera
from speechRecognition import record_audio, recognize_speech
from message import send_bot_message


def control_led(mode, arduino):
    arduino.write((mode + "\n").encode())

def face_confidence(face_distance, face_match_threshold=0.6):
    range = (1.0 - face_match_threshold)
    linear_val = (1.0 - face_distance) / (range * 2.0)

    if face_distance > face_match_threshold:
        return str(round(linear_val * 100, 2))
    else:
        value = (linear_val + ((1.0 - linear_val) *
                 math.pow((linear_val - 0.5) * 2, 0.2))) * 100
        return str(round(value, 2))

class Face:
    def __init__(self):
        self.face_locations = []
        self.face_encodings = []
        self.face_names = []
        self.known_face_encodings = []
        self.known_face_names = []
        self.process_current_frame = True
        self.encode_faces()

    def encode_faces(self):
        for image in os.listdir('faces'):
            face_image = face_recognition.load_image_file(f'faces/{image}')
            face_encoding = face_recognition.face_encodings(face_image)[0]
            self.known_face_encodings.append(face_encoding)
            self.known_face_names.append(image.split('.')[0])

    def face_recognition_process(self, frame):
        if self.process_current_frame:
            small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
            rgb_small_frame = np.ascontiguousarray(small_frame[:, :, ::-1])

            self.face_locations = face_recognition.face_locations(rgb_small_frame)
            self.face_encodings = face_recognition.face_encodings(rgb_small_frame, self.face_locations)

            self.face_names = []
            for face_encoding in self.face_encodings:
                matches = face_recognition.compare_faces(self.known_face_encodings, face_encoding)
                name = 'Unknown'
                confidence = '0'

                face_distances = face_recognition.face_distance(self.known_face_encodings, face_encoding)
                best_match_index = np.argmin(face_distances)

                if matches[best_match_index]:
                    name = self.known_face_names[best_match_index]
                    confidence = face_confidence(face_distances[best_match_index])
                    if float(confidence) < 90:
                        name = 'Unknown'
                        confidence = 'Unknown'
                else:
                    name = 'Unknown'
                    confidence = 'Unknown'

                self.face_names.append(f'{name} ({confidence}%)')

        self.process_current_frame = not self.process_current_frame

        return self.face_names, self.face_locations

class EmotionDetector:
    def __init__(self):
        self.model = self.create_model()
        self.model.load_weights('model/model.h5')
        self.emotion_dict = {0: "Angry", 1: "Disgusted", 2: "Fearful",
                             3: "Happy", 4: "Neutral", 5: "Sad", 6: "Surprised"}
        cv2.ocl.setUseOpenCL(False)

    def create_model(self):
        model = tf.keras.models.Sequential([
            tf.keras.layers.Conv2D(32, kernel_size=(3, 3), activation='relu', input_shape=(48, 48, 1)),
            tf.keras.layers.Conv2D(64, kernel_size=(3, 3), activation='relu'),
            tf.keras.layers.MaxPooling2D(pool_size=(2, 2)),
            tf.keras.layers.Dropout(0.25),
            tf.keras.layers.Conv2D(128, kernel_size=(3, 3), activation='relu'),
            tf.keras.layers.MaxPooling2D(pool_size=(2, 2)),
            tf.keras.layers.Conv2D(128, kernel_size=(3, 3), activation='relu'),
            tf.keras.layers.MaxPooling2D(pool_size=(2, 2)),
            tf.keras.layers.Dropout(0.25),
            tf.keras.layers.Flatten(),
            tf.keras.layers.Dense(1024, activation='relu'),
            tf.keras.layers.Dropout(0.5),
            tf.keras.layers.Dense(7, activation='softmax')
        ])
        return model

    def detect_emotion(self, face_img):
        gray = cv2.cvtColor(face_img, cv2.COLOR_BGR2GRAY)
        resized_img = cv2.resize(gray, (48, 48))
        cropped_img = np.expand_dims(np.expand_dims(resized_img, -1), 0)
        prediction = self.model.predict(cropped_img)
        maxindex = int(np.argmax(prediction))
        return self.emotion_dict[maxindex]

def Face_Emotion_Recognition(arduino):
    camera = find_working_camera()
    cap = cv2.VideoCapture(camera)
    if not cap.isOpened():
        sys.exit("Cannot open camera")

    face = Face()
    emotion_detector = EmotionDetector()
    recognized_name = "UnKnown"

    while True:
        ret, frame = cap.read()
        if not ret or frame is None:
            print("Failed to capture frame.")
            continue

        frame = cv2.flip(frame, 1)
        frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)

        face_names, face_locations = face.face_recognition_process(frame)
        face_detected = len(face_locations) > 0

        if face_detected:
            for (top, right, bottom, left), name in zip(face_locations, face_names):
                top *= 4
                right *= 4
                bottom *= 4
                left *= 4

                face_img = frame[top:bottom, left:right]
                
                detected_emotion = emotion_detector.detect_emotion(face_img)

                if name.split()[0] != 'Unknown':
                    recognized_name = name.split()[0]
                    emotion = detected_emotion
                else:
                    try:
                        control_led('voice', arduino)
                        Voice_out("I don't recognize you, can I know your name please?", arduino)
                        audio = record_audio()
                        text = recognize_speech(audio)
                        if text == "":
                            text = "no"
                        response = get_response(f"user response to 'Can I know your name please?' is - {text}, if it contains a name then return the name only else return just one word - Unknown")
                        response = response.strip()
                        if response.lower() not in ['unknown', 'tessa', 'okay']:
                            if len(face_recognition.face_encodings(frame)) > 0:
                                # Save the image only if a face is detected
                                _, img_encoded = cv2.imencode('.jpg', frame)
                                with open(f'faces/{response}.jpg', 'wb') as f:
                                    f.write(img_encoded)
                                recognized_name = response
                                emotion = detected_emotion
                            else:
                                recognized_name = response
                                emotion = detected_emotion
                                Voice_out('I didn’t get your face correctly.', arduino)
                        else:
                            recognized_name = "Unknown"
                            emotion = detected_emotion
                    except Exception as e:
                        # print(f"An error occurred: {e}")
                        Voice_out('I didn’t get your face correctly.', arduino)

            query = f'My name is {recognized_name} and my emotion is {emotion}. Talk to me.' if recognized_name != "Unknown" else f"I am feeling {emotion}. Talk to me"
            if recognized_name not in ["Samartha"] and recognized_name != None:
                send_bot_message(f'000 HI, {recognized_name} 👋')
            response = get_response(query)
            control_led('voice', arduino)
            Voice_out(response, arduino)
            break  # Exit the loop once a face is detected

        # cv2.imshow('Face and Emotion Recognition', frame)
        # Exit if 'q' key is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        

    # Release the camera and close all OpenCV windows when done
    cap.release()
    cv2.destroyAllWindows()

