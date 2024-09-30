import cv2


def find_working_camera(max_index=3):
  
    for i in range(max_index-1, -1, -1):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            print(f"Camera found at index {i}")
            return i
        cap.release()
    print("No working camera found.")
    return None