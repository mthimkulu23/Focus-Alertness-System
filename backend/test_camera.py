import cv2
import time

# Try different indices if 0 doesn't work (0, 1, 2, etc.)
VIDEO_SOURCE = 0

print(f"Attempting to open camera source: {VIDEO_SOURCE}")
cap = cv2.VideoCapture(VIDEO_SOURCE)

if not cap.isOpened():
    print(f"Error: Could not open video source {VIDEO_SOURCE}. Is it in use by another app or not connected?")
else:
    print(f"Successfully opened video source {VIDEO_SOURCE}.")
    # Try to read one frame
    ret, frame = cap.read()
    if ret:
        print(f"Successfully read one frame. Frame dimensions: {frame.shape[1]}x{frame.shape[0]} (width x height)")
        # Optionally display the frame for a short time
        cv2.imshow('Test Frame', frame)
        cv2.waitKey(2000) # Show for 2 seconds
        cv2.destroyAllWindows()
    else:
        print("Error: Could not read frame from camera.")
    cap.release()
    print("Camera released.")

print("\n--- Testing Haar Cascade Loading ---")
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

