import numpy as np
import cv2
import threading
from deepface import DeepFace
import sys
import os
import logging
from voiceOut import Voice_out
from cameraindex import find_working_camera
import ctypes

if True:  # Include project path
    ROOT = os.path.dirname(os.path.abspath(__file__)) + "/../"
    CURR_PATH = os.path.dirname(os.path.abspath(__file__)) + "/"
    sys.path.append(ROOT)
    import utils.lib_images_io as lib_images_io
    import utils.lib_plot as lib_plot
    import utils.lib_commons as lib_commons
    from utils.lib_openpose import SkeletonDetector
    from utils.lib_tracker import Tracker
    from utils.lib_classifier import ClassifierOnlineTest

SRC_DATA_TYPE = "webcam"
SRC_DATA_PATH = "0"
SRC_MODEL_PATH = "model/trained_classifier.pickle"
logging.basicConfig(level=logging.WARNING)

cfg_all = lib_commons.read_yaml(ROOT + "config/config.yaml")
cfg = cfg_all["s5_test.py"]

CLASSES = np.array(cfg_all["classes"])
SKELETON_FILENAME_FORMAT = cfg_all["skeleton_filename_format"]

# Action recognition: number of frames used to extract features.
WINDOW_SIZE = int(cfg_all["features"]["window_size"])

# If data_type is webcam, set the max frame rate.
SRC_WEBCAM_MAX_FPS = float(cfg["settings"]["source"]["webcam_max_framerate"])

# Openpose settings
OPENPOSE_MODEL = cfg["settings"]["openpose"]["model"]
OPENPOSE_IMG_SIZE = cfg["settings"]["openpose"]["img_size"]

# Display settings
img_disp_desired_rows = int(cfg["settings"]["display"]["desired_rows"])

# -- Function

class MultiPersonClassifier(object):
    def __init__(self, model_path, classes):
        self.dict_id2clf = {}  # human id -> classifier of this person
        # Define a function for creating classifier for new people.
        self._create_classifier = lambda human_id: ClassifierOnlineTest(
            model_path, classes, WINDOW_SIZE, human_id)

    def classify(self, dict_id2skeleton):
        # Clear people not in view
        old_ids = set(self.dict_id2clf)
        cur_ids = set(dict_id2skeleton)
        humans_not_in_view = list(old_ids - cur_ids)
        for human in humans_not_in_view:
            del self.dict_id2clf[human]

        # Predict each person's action
        id2label = {}
        for id, skeleton in dict_id2skeleton.items():
            if id not in self.dict_id2clf:  # add this new person
                self.dict_id2clf[id] = self._create_classifier(id)
            classifier = self.dict_id2clf[id]
            id2label[id] = classifier.predict(skeleton)  # predict label

        return id2label

    def get_classifier(self, id):
        if len(self.dict_id2clf) == 0:
            return None
        if id == 'min':
            id = min(self.dict_id2clf.keys())
        return self.dict_id2clf[id]


def remove_skeletons_with_few_joints(skeletons):
    good_skeletons = []
    for skeleton in skeletons:
        px = skeleton[2:2 + 13 * 2:2]
        py = skeleton[3:2 + 13 * 2:2]
        num_valid_joints = len([x for x in px if x != 0])
        num_leg_joints = len([x for x in px[-6:] if x != 0])
        total_size = max(py) - min(py)
        if num_valid_joints >= 5 and total_size >= 0.1 and num_leg_joints >= 0:
            good_skeletons.append(skeleton)
    return good_skeletons


def draw_result_img(img_disp, ith_img, humans, dict_id2skeleton,
                    skeleton_detector, multiperson_classifier, dict_id2label, scale_h):
    if img_disp is None:
        print(f"Warning: Frame {ith_img} could not be captured.")
        return None

    # Resize to a proper size for display
    r, c = img_disp.shape[0:2]
    desired_cols = int(1.0 * c * (img_disp_desired_rows / r))
    img_disp = cv2.resize(img_disp, dsize=(desired_cols, img_disp_desired_rows))

    # Draw all people's skeleton
    skeleton_detector.draw(img_disp, humans)

    # Draw bounding box and label of each person
    if len(dict_id2skeleton and dict_id2label):
        for id, label in dict_id2label.items():
            skeleton = dict_id2skeleton[id]
            # scale the y data back to original
            skeleton[1::2] = skeleton[1::2] / scale_h
            lib_plot.draw_action_result(img_disp, id, skeleton, label)

    # Add blank to the left for displaying prediction scores of each class
    img_disp = lib_plot.add_white_region_to_left_of_image(img_disp)

    cv2.putText(img_disp, "Frame:" + str(ith_img),
                (20, 20), fontScale=1.5, fontFace=cv2.FONT_HERSHEY_PLAIN,
                color=(0, 0, 0), thickness=2)

    # Draw predicting score for only 1 person
    if len(dict_id2skeleton):
        classifier_of_a_person = multiperson_classifier.get_classifier(id='min')
        classifier_of_a_person.draw_scores_onto_image(img_disp)
    return img_disp


def get_the_skeleton_data_to_save_to_disk(dict_id2skeleton, dict_id2label):
    skels_to_save = []
    for human_id in dict_id2skeleton.keys():
        label = dict_id2label[human_id]
        skeleton = dict_id2skeleton[human_id]
        skels_to_save.append([[human_id, label] + skeleton.tolist()])
    return skels_to_save

def control_led(mode, arduino):
    arduino.write((mode + "\n").encode())

def Action_Detection(arduino):
    # -- Detector, tracker, classifier
    skeleton_detector = SkeletonDetector(OPENPOSE_MODEL, OPENPOSE_IMG_SIZE)
    multiperson_tracker = Tracker()
    multiperson_classifier = MultiPersonClassifier(SRC_MODEL_PATH, CLASSES)

    # Initialize webcam capture
    camera = find_working_camera()
    cap = cv2.VideoCapture(camera)  # Use 0 for default webcam
    if not cap.isOpened():
        print("Error: Could not open webcam.")
        return

    # img_displayer = lib_images_io.ImageDisplayer()

    ith_img = -1
    dict_id2label = {}  # Initialize dict_id2label here
    action_thread = threading.current_thread()

    # Set the window name
    window_name = "Camera Feed"

    while cap.isOpened() and getattr(action_thread, "do_run", True):
        # -- Read image
        ret, img = cap.read()
        if not ret:
            print("Error: Could not read frame from webcam.")
            break

        ith_img += 1
        img_disp = img.copy()
        # print(f"\nProcessing {ith_img}th image ...")

        # -- Detect skeletons
        humans = skeleton_detector.detect(img)
        skeletons, scale_h = skeleton_detector.humans_to_skels_list(humans)
        skeletons = remove_skeletons_with_few_joints(skeletons)

        # -- Track people
        dict_id2skeleton = multiperson_tracker.track(skeletons)  # int id -> np.array() skeleton

        # -- Recognize action of each person
        if len(dict_id2skeleton):
            dict_id2label = multiperson_classifier.classify(dict_id2skeleton)
        else:
            dict_id2label = {}  # Ensure dict_id2label is always initialized

        # -- Draw
        img_disp = draw_result_img(img_disp, ith_img, humans, dict_id2skeleton,
                                    skeleton_detector, multiperson_classifier, dict_id2label, scale_h)

        # Resize the image
        desired_width = 960
        desired_height = 720
        img_disp = cv2.resize(img_disp, (desired_width, desired_height))

        # Print label of a person
        if len(dict_id2skeleton):
            min_id = min(dict_id2skeleton.keys())
            print("predicted label is :", dict_id2label[min_id])
            if dict_id2label[min_id] == 'punch':
                Voice_out('oh oh dont do that. violence is strictly prohibited in this premises.', arduino)
                control_led('action_mode', arduino)

        # -- Display image
        # cv2.imshow(window_name, img_disp)

        # Make the window always on top (Windows specific)
        hwnd = ctypes.windll.user32.FindWindowW(None, window_name)
        ctypes.windll.user32.SetWindowPos(hwnd, -1, 0, 0, 0, 0, 0x0001)

        if cv2.waitKey(1) == 27:  # Press 'ESC' to exit
            break

    cap.release()
    cv2.destroyAllWindows()
