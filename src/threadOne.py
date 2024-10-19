import cv2
import numpy as np
import face_recognition
import os
import math
from generativeai import get_response
from voiceOut import Voice_out
from message import send_bot_message, send_user_message
import re
import requests
import glob
import speech_recognition as sr
from cameraindex import find_working_camera
import random

recognizer = sr.Recognizer()

class Face:
    def __init__(self):
        self.face_locations = []
        self.face_encodings = []
        self.face_names = []
        self.known_face_encodings = []
        self.known_face_names = []
        self.process_current_frame = True
        self.last_face_encoding = None
        self.encode_faces()

    def encode_faces(self):
        for image in os.listdir('faces'):
            face_image = face_recognition.load_image_file(f'faces/{image}')
            face_encoding = face_recognition.face_encodings(face_image)[0]
            self.known_face_encodings.append(face_encoding)
            self.known_face_names.append(image.split('.')[0])

    def update_faces(self):
        current_face_images = {image.split('.')[0] for image in os.listdir('faces')}
        to_remove = [i for i, name in enumerate(self.known_face_names) if name not in current_face_images]
        
        for index in sorted(to_remove, reverse=True):
            del self.known_face_encodings[index]
            del self.known_face_names[index]

        existing_names = set(self.known_face_names)
        for image in os.listdir('faces'):
            name = image.split('.')[0]
            if name not in existing_names: 
                face_image = face_recognition.load_image_file(f'faces/{image}')
                face_encoding = face_recognition.face_encodings(face_image)
                if face_encoding: 
                    self.known_face_encodings.append(face_encoding[0])
                    self.known_face_names.append(name)
        
        print("Known face names:", self.known_face_names)
    
    def face_recognition(self, frame):
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

                if len(face_distances) > 0:
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
                else:
                    name = 'Unknown'
                    confidence = 'Unknown'
                
                self.face_names.append(f'{name} ({confidence}%)')

        self.process_current_frame = not self.process_current_frame
        return self.face_names, self.face_locations

def face_confidence(face_distance, face_match_threshold=0.6):
    range = (1.0 - face_match_threshold)
    linear_val = (1.0 - face_distance) / (range * 2.0)

    if face_distance > face_match_threshold:
        return str(round(linear_val * 100, 2))
    else:
        value = (linear_val + ((1.0 - linear_val) *
                               math.pow((linear_val - 0.5) * 2, 0.2))) * 100
        return str(round(value, 2))



def face_recognition_process(arduino, user_message_queue, bot_message_queue):
    index = find_working_camera()
    cap = cv2.VideoCapture(index)
    face_recognizer = Face()
    frame_count = 0
    last_detected_faces = []
    last_closest_face = None  # Track the last closest face
    unknown_counts = 0


    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to capture frame.")
            continue

        frame = cv2.flip(frame, 1)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Process every 5th frame to reduce load
        frame_count += 1
        if frame_count % 5 == 0:
            face_names, face_locations = face_recognizer.face_recognition(frame)
            closest_face = None
            closest_area = float('inf')  # Initialize with infinity to find the minimum area
            closest_face_position = None

            for (top, right, bottom, left), name in zip(face_locations, face_names):
                top *= 4
                right *= 4
                bottom *= 4
                left *= 4

                # Calculate the rectangle area
                width = right - left
                height = bottom - top
                area = width * height

                # Check if this face is the closest
                if top < closest_area:
                    closest_area = top
                    closest_face = name  # Store the name of the closest person
                    closest_face = re.sub(r'\s*\(.*?\)\s*', '', closest_face)
                    closest_face_position = (left + right) // 2, (top + bottom) // 2

                # cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)
                # cv2.putText(frame, f'{name} - Area: {area}', (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

            # Check if the closest face has changed
            if closest_face and closest_face.startswith('dude'):
                continue


            elif closest_face and closest_face != last_closest_face and closest_face.lower() != 'unknown':
                last_closest_face = closest_face  # Update the last closest face

                # Only trigger response if the closest person is not the last detected face
                if closest_face not in last_detected_faces:
                    last_detected_faces = face_names.copy()  # Update last detected faces
                    formatted_faces_str = f'detected face - {closest_face}, Talk to him as the competition recaches its end.'
                    response = get_response(formatted_faces_str)
                    send_bot_message(f"000 HI, {closest_face} 👋", bot_message_queue)
                    Voice_out(response, arduino)


            elif closest_face == 'Unknownnguy':
                unknown_counts = unknown_counts + 1
                if unknown_counts > 5:
                    unknown_counts = 0   
                    try:
                        try:
                            requests.get('http://127.0.0.1:5000/stop')
                            print('stopped')
                        except requests.exceptions.RequestException as e:
                            print(f"Failed to send position data: {e}")
                            requests.get('http://127.0.0.1:5000/activate')
                            break
                        Voice_out("I don't recognize you, can I know your name please.", arduino)
                        print("I don't recognize you, can I know your name please.")
                        try:
                            with sr.Microphone() as source:
                                print('Listening....')
                                audio = recognizer.listen(source, timeout=15, phrase_time_limit=10)  # Increased timeout and phrase time limit
                                print('Recorded...')
                                text = recognizer.recognize_google(audio)
                                send_user_message(text, user_message_queue)
                                print(f"You said: {text}")
                        except sr.UnknownValueError:
                            text=""
                        except sr.RequestError:
                                text=""
                        if text == "":
                            text = "no"
                        res = get_response(f"find a name from the text if exists, and give that name only in one word - {text}, if it contains no name then give only one word - Unknown. remember giving answer in one word is important, for example if text is 'my name is name' then give 'name'.")
                        print(res)
                        res = res.strip()
                        if "unknown" not in res.lower() and res.lower() not in ['sentosa', 'okay']:
                            if len(face_recognition.face_encodings(frame)) > 0:
                                _, img_encoded = cv2.imencode('.jpg', frame)
                                with open(f'faces/{res}.jpg', 'wb') as f:
                                    f.write(img_encoded)
                                closest_face = res
                                face_recognizer.update_faces()
                            else:
                                closest_face = res
                                Voice_out('I didn’t get your face correctly.', arduino)
                        else:
                            if len(face_recognition.face_encodings(frame)) > 0:
                                file_to_delete = glob.glob(os.path.join('faces', 'dude*'))
                                if file_to_delete:
                                    os.remove(file_to_delete[0])
                                prefix = random.randint(10, 99)
                                _, img_encoded = cv2.imencode('.jpg', frame)
                                with open(f'faces/dude{prefix}.jpg', 'wb') as f:
                                    f.write(img_encoded)
                                closest_face = 'Unknown'
                                face_recognizer.update_faces()
                            else:
                                closest_face = 'Unknown'
                                Voice_out('I didn’t get your face correctly.', arduino)

                    except Exception as e:
                        print(f"An error occurred: {e}")
                        Voice_out('sorry, I did not get your face correctly.', arduino)
                    query = f'My name is {closest_face} . Hello.' if closest_face != "Unknown" else f"hello"
                    if closest_face not in ["Sentosa"] and closest_face != None:
                        send_bot_message(f'000 HI, {closest_face} 👋', bot_message_queue)
                    response = get_response(query)
                    Voice_out(response, arduino)
                    last_closest_face = closest_face
                    try:
                        requests.get('http://127.0.0.1:5000/activate')
                    except requests.exceptions.RequestException as e:
                        print(f"Failed to reactivate interactions: {e}")

            if closest_face_position:
                    data = {'x': closest_face_position[0], 'y': closest_face_position[1]}
                    try:
                        requests.post('http://127.0.0.1:5000/update_position', json=data)
                    except requests.exceptions.RequestException as e:
                        print(f"Failed to send position data: {e}")
            else:
                data = {'x':0, 'y': 0}
                try:
                     requests.post('http://127.0.0.1:5000/update_position', json=data)
                except requests.exceptions.RequestException as e:
                    print(f"Failed to send position data: {e}")


        # Show the frame with recognized faces
        cv2.imshow('Face Recognition', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
