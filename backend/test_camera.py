import cv2
import time

# Try different indices if 0 doesn't work (0, 1, 2, etc.)
VIDEO_SOURCE = 0
TARGET_DISPLAY_HEIGHT = 720 # Target height for the displayed frame

print(f"Attempting to open camera source: {VIDEO_SOURCE}")
cap = cv2.VideoCapture(VIDEO_SOURCE)

if not cap.isOpened():
    print(f"Error: Could not open video source {VIDEO_SOURCE}. Is it in use by another app or not connected?")
else:
    print(f"Successfully opened video source {VIDEO_SOURCE}.")
    # Try to read one frame
    ret, frame = cap.read()
    if ret:
        print(f"Successfully read one frame. Original Frame dimensions: {frame.shape[1]}x{frame.shape[0]} (width x height)")

        # Calculate new width to maintain aspect ratio
        original_height, original_width = frame.shape[:2]
        if original_height > 0: # Avoid division by zero
            aspect_ratio = original_width / original_height
            new_width = int(TARGET_DISPLAY_HEIGHT * aspect_ratio)
            resized_frame = cv2.resize(frame, (new_width, TARGET_DISPLAY_HEIGHT))
            print(f"Resized Frame dimensions for display: {new_width}x{TARGET_DISPLAY_HEIGHT} (width x height)")
        else:
            resized_frame = frame
            print("Warning: Original frame height is zero, skipping resize.")

        # Display the resized frame for a short time
        cv2.imshow('Test Frame', resized_frame)
        cv2.waitKey(2000) # Show for 2 seconds
        cv2.destroyAllWindows()
    else:
        print("Error: Could not read frame from camera.")
    cap.release()
    print("Camera released.")

print("\n--- Testing Haar Cascade Loading ---")
# --- Load Pre-trained Face Detector ---
# OpenCV's Haar Cascade for face detection
# This XML file needs to be present in the same directory as app.py
# You can download it from:
# https://github.com/opencv/opencv/blob/master/data/haarcascades/haarcascade_frontalface_default.xml
try:
    # This path assumes haarcascade_frontalface_default.xml is in the same directory as this script.
    # In a Flask app, it's typically alongside app.py, but for this test script, it means
    # in the same folder as test_camera.py
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    if face_cascade.empty():
        print("Error: Face cascade XML file is empty or not loaded correctly. Make sure it's in the same directory as this script.")
    else:
        print("Face cascade XML file loaded successfully.")
except Exception as e:
    print(f"Error loading face cascade: {e}")

