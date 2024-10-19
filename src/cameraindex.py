import cv2


def find_working_camera():
  
    for i in range(0, 2, 1):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            return i
        cap.release()
    print("No working camera found.")
    return 0