import numpy as np
import cv2
import threading
import tensorflow as tf
from generativeai import get_response
from voiceOut import Voice_out
from speechRecognition import record_audio, recognize_speech
import time

# Function to control Arduino LEDs
def control_led(mode, arduino):
    arduino.write((mode + "\n").encode())

# face_r = Face()
class EmotionDetector:
    def __init__(self):
        self.model = self.create_model()
        self.model.load_weights('model.h5')
        self.emotion_dict = {0: "Angry", 1: "Disgusted", 2: "Fearful", 3: "Happy", 4: "Neutral", 5: "Sad", 6: "Surprised"}
        cv2.ocl.setUseOpenCL(False)
        self.stop_thread = False

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

    def detect_emotion(self, arduino):
        cap = cv2.VideoCapture(1)
        facecasc = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')

        thread = threading.current_thread()

        while getattr(thread, "do_run", True)and not self.stop_thread:
            ret, frame = cap.read()
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = facecasc.detectMultiScale(gray,scaleFactor=1.3, minNeighbors=5)
            # face_thread = threading.Thread(target=face_r.face_recognition_process, args=(frame,))
            # face_thread.start()
            for (x, y, w, h) in faces:
                cv2.rectangle(frame, (x, y-50), (x+w, y+h+10), (255, 0, 0), 2)
                roi_gray = gray[y:y + h, x:x + w]
                cropped_img = np.expand_dims(np.expand_dims(cv2.resize(roi_gray, (48, 48)), -1), 0)
                prediction = self.model.predict(cropped_img)
                maxindex = int(np.argmax(prediction))
                cv2.putText(frame, self.emotion_dict[maxindex], (x+20, y-60), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
                control_led(self.emotion_dict[maxindex], arduino)
                if(self.emotion_dict[maxindex]):
                    response = get_response(f'iam feeling {self.emotion_dict[maxindex]}. talk to me')
                    voice_thread = threading.Thread(target=Voice_out, args=(response, arduino))
                    voice_thread.start()
                    voice_thread.join()
                control_led("emotion_mode", arduino)
                print('sent')
                    
            cv2.imshow("Frame", frame)
            key = cv2.waitKey(1) & 0xFF

            if key == ord("q"):
                break

        cap.release()
        cv2.destroyAllWindows()