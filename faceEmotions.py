import numpy as np
import cv2
import threading
import tensorflow as tf
import face_recognition
import os
import math
import time
from emotionVoice import Voice_out  # Assuming this function outputs audio based on the input text
from generativeai import get_response  # Assuming this function generates a response text
import sys

def control_led(mode, arduino):
    arduino.write((mode + "\n").encode())

# Function to calculate face confidence
def face_confidence(face_distance, face_match_threshold=0.6):
    range = (1.0 - face_match_threshold)
    linear_val = (1.0 - face_distance) / (range * 2.0)

    if face_distance > face_match_threshold:
        return str(round(linear_val * 100, 2))
    else:
        value = (linear_val + ((1.0 - linear_val) * math.pow((linear_val - 0.5) * 2, 0.2))) * 100
        return str(round(value, 2))

# Face recognition class
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

# Emotion detection class
class EmotionDetector:
    def __init__(self):
        self.model = self.create_model()
        self.model.load_weights('model.h5')
        self.emotion_dict = {0: "Angry", 1: "Disgusted", 2: "Fearful", 3: "Happy", 4: "Neutral", 5: "Sad", 6: "Surprised"}
        cv2.ocl.setUseOpenCL(False)

    def create_model(self):
        model = tf.keras.models.Sequential([
            tf.keras.layers.Conv2D(32, kernel_size=(3, 3), activation='relu', input_shape=(48,48,1)),
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

# Main function to integrate face recognition and emotion detection
def Face_Emotion_Recognition(arduino):
    cap = cv2.VideoCapture(1)
    if not cap.isOpened():
        sys.exit("Cannot open camera")

    face = Face()
    emotion_detector = EmotionDetector()

    thread = threading.current_thread()

    while getattr(thread, "do_run", True):
        ret, frame = cap.read()
        frame = cv2.flip(frame, 1)

        if not ret:
            print("Can't receive frame (stream end?). Exiting ...")
            break

        face_names, face_locations = face.face_recognition_process(frame)
        face_detected = len(face_locations) > 0  # Check if any face is detected

        if face_detected:
            start_time = time.time()  # Start timing for 5 seconds analysis
            recognized_name = None
            emotion = "Neutral"  # Initialize emotion to a default value

            while time.time() - start_time < 5:  # Continue for 5 seconds or until a known face is found
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
                        break  # Exit the loop as soon as a known face is recognized

                # If a known face is found, break the outer loop
                if recognized_name:
                    break

                # Refresh frame and continue checking within the 5 seconds
                ret, frame = cap.read()
                frame = cv2.flip(frame, 1)
                if not ret:
                    print("Can't receive frame (stream end?). Exiting ...")
                    break

                face_names, face_locations = face.face_recognition_process(frame)

            # If no recognized name was found within 5 seconds, default to "Unknown"
            if not recognized_name:
                recognized_name = "Unknown"
                emotion = detected_emotion  # Use the last detected emotion

            # Prepare the query for response
            if recognized_name != "Unknown":
                query = f'My name is {recognized_name} and my emotion is {emotion}. Talk to me.'
            else:
                query = f'I am feeling {emotion}. Talk to me.'

            response = get_response(query)
            control_led('voice', arduino)
            voice_thread = threading.Thread(target=Voice_out, args=(response, arduino))
            voice_thread.start()
            # control_led('emotion_mode', arduino)

        cv2.imshow('Face and Emotion Recognition', frame)

        if cv2.waitKey(1) == 27:  # Press 'ESC' to exit
            break

    cap.release()
    cv2.destroyAllWindows()

