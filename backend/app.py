import cv2
import time
from flask import Flask, Response, jsonify, render_template
import numpy as np # Import numpy for image processing
import random # For simulating random events

app = Flask(__name__)

# --- Configuration ---
# Use 0 for default webcam, or a video file path
VIDEO_SOURCE = 0
# Interval for updating analytics (in seconds)
ANALYTICS_UPDATE_INTERVAL = 2 # Reduced for faster UI updates

# --- Global Variables for Analytics ---
global_face_count = 0
global_sleeping_status = "No person detected"
global_focus_score = 0.0
global_unauthorized_activity_status = "None Detected"
global_copy_attempt_status = "None Detected"
global_proctoring_alert_status = "No Violations"

# --- AI Simulation/Detection Variables ---
last_person_detected_time = time.time()
simulated_drowsiness_level = 0 # 0-100, higher means more drowsy
last_gaze_direction = "center" # Simulated: "center", "left", "right", "up", "down"
gaze_away_duration = 0
max_gaze_away_duration = 3 # seconds before unauthorized activity

# Timestamp of the last analytics update
last_analytics_update_time = time.time()
last_activity_check_time = time.time() # Used for overall simulated events


try:
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    if face_cascade.empty():
        print("Error: Could not load face cascade XML file. Please ensure it's in the same directory as app.py.")
except Exception as e:
    print(f"Error loading face cascade: {e}")
    face_cascade = None 

# --- Video Capture Initialization ---
print(f"Attempting to open camera source: {VIDEO_SOURCE}")
camera = cv2.VideoCapture(VIDEO_SOURCE)
if not camera.isOpened():
    print(f"Error: Could not open video source {VIDEO_SOURCE}. Is it in use by another app or not connected? Please check permissions.")
    exit() # Exit if camera cannot be opened
else:
    print(f"Successfully opened video source {VIDEO_SOURCE}.")

# --- AI Detection & Simulation Logic (Enhanced) ---
def perform_ai_detection(frame, faces):
    """
    Performs basic AI-like detection based on face presence and simulated behaviors.
    For a real system, advanced computer vision (e.g., dlib, mediapipe, deep learning models)
    would be integrated here.
    """
    global global_face_count, global_sleeping_status, global_focus_score, \
           global_unauthorized_activity_status, global_copy_attempt_status, \
           global_proctoring_alert_status, last_person_detected_time, \
           simulated_drowsiness_level, last_gaze_direction, gaze_away_duration

    current_time = time.time()

    # 1. Update Face Count
    global_face_count = len(faces)

    if global_face_count > 0:
        last_person_detected_time = current_time
        # Reset activity flags if a person is clearly present and focused (simulated)
        # These will be re-evaluated below
        global_unauthorized_activity_status = "None Detected"
        global_copy_attempt_status = "None Detected"

        # --- Simulate Drowsiness (very basic) ---
        # In a real app: Analyze eye-aspect ratio (EAR) over time
        # Here: Simulate based on random chance or prolonged "stillness"
        if random.random() < 0.01: # 1% chance per frame to change drowsiness
            if simulated_drowsiness_level < 100 and random.random() < 0.6: # 60% chance to increase
                simulated_drowsiness_level += random.randint(1, 5)
            elif simulated_drowsiness_level > 0: # 40% chance to decrease
                simulated_drowsiness_level -= random.randint(1, 5)
            simulated_drowsiness_level = max(0, min(100, simulated_drowsiness_level)) # Keep within 0-100

        if simulated_drowsiness_level > 70:
            global_sleeping_status = "Likely Sleeping (AI Simulated)"
            global_proctoring_alert_status = "Drowsiness Detected!"
        elif simulated_drowsiness_level > 40:
            global_sleeping_status = "Potentially Drowsy (AI Simulated)"
            global_proctoring_alert_status = "Low Alertness"
        else:
            global_sleeping_status = "Awake (AI Simulated)"
            global_proctoring_alert_status = "No Violations" # Default

        # --- Simulate Gaze Direction / Attention (very basic) ---
        # In a real app: Head pose estimation (e.g., from facial landmarks)
        if random.random() < 0.02: # 2% chance to change gaze direction
            possible_gazes = ["center", "left", "right", "up", "down"]
            last_gaze_direction = random.choice(possible_gazes)

        if last_gaze_direction != "center" and random.random() < 0.05: # 5% chance to accumulate gaze_away_duration
            gaze_away_duration += 1
        else:
            gaze_away_duration = 0 # Reset if returns to center or not away

        if gaze_away_duration > max_gaze_away_duration:
            global_unauthorized_activity_status = f"Gaze Away for {gaze_away_duration}s (Simulated)"
            global_proctoring_alert_status = "Attention Diverted!"
        elif global_unauthorized_activity_status != "System Access Violation": # Don't overwrite higher priority alert
             global_unauthorized_activity_status = "None Detected"


        # --- Simulate Focus Score ---
        # Combining face presence and inverse drowsiness
        global_focus_score = max(0.0, 100.0 - simulated_drowsiness_level - (gaze_away_duration * 10))
        global_focus_score = min(100.0, max(0.0, global_focus_score))


        # --- Simulate Copy Attempt (Multi-person Detection) ---
        # In a real app: More advanced social distancing or prohibited object detection
        if global_face_count > 1:
            global_copy_attempt_status = f"Multiple Persons Detected ({global_face_count})!"
            global_proctoring_alert_status = "Potential Cheating!"
        else:
            global_copy_attempt_status = "None Detected"


        # --- Draw Rectangles on Faces ---
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
            cv2.putText(frame, "Person", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

    else: # No person detected
        time_since_last_person = current_time - last_person_detected_time
        if time_since_last_person > 5: # If no person for 5+ seconds
            global_sleeping_status = "No person detected - (Absent)"
            global_proctoring_alert_status = "Student Absent!"
            global_unauthorized_activity_status = "No Person Detected"
        else:
            global_sleeping_status = "No person detected" # Just temporarily absent
            global_unauthorized_activity_status = "None Detected" # Clear if person might just be briefly out of frame

        global_focus_score = 0.0
        global_copy_attempt_status = "None Detected"
        # Keep proctoring alert if it was set for absence, otherwise reset to no violations
        if global_proctoring_alert_status != "Student Absent!":
            global_proctoring_alert_status = "No Violations"


    # --- Simulate Tab Switching / External Access (conceptual) ---
    # This feature requires OS-level integration, not possible in pure browser/Flask.
    # We continue a random simulation, but in a real app, this would be triggered
    # by actual system events.
    if random.random() < 0.0005: # Very low chance per frame
        global_proctoring_alert_status = random.choice([
            "Tab Switched! (Concept)",
            "External App Detected! (Concept)",
            "System Violation! (Concept)"
        ])
        global_unauthorized_activity_status = "System Access Violation (Concept)"


# --- Generator for Video Streaming ---
def generate_frames():
    """
    Generates MJPEG frames from the webcam, performs face detection,
    and updates global analytics variables.
    """
    global camera, global_face_count

    # Flag to print frame dimensions only once
    first_frame_read = False

    while True:
        success, frame = camera.read()
        if not success:
            print("Error: Failed to read frame from camera. Attempting to re-open.")
            # Attempt to re-open camera if it failed to read
            camera.release() # Release existing camera object
            camera = cv2.VideoCapture(VIDEO_SOURCE)
            if not camera.isOpened():
                print(f"Critial Error: Could not re-open video source {VIDEO_SOURCE}. Exiting frame generation.")
                break # Exit loop if camera cannot be re-opened
            time.sleep(0.1) # Wait a bit before trying again
            continue # Try reading frame again

        if not first_frame_read:
            if frame is not None:
                print(f"Successfully read first frame. Frame dimensions: {frame.shape[1]}x{frame.shape[0]} (width x height)")
                first_frame_read = True
            else:
                print("Warning: First frame was None despite success=True. Retrying...")
                continue # Skip processing this frame and try again

        # Perform AI detection and update global variables
        # No need to pass frame and faces explicitly as globals are used
        perform_ai_detection(frame, face_cascade.detectMultiScale(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)))

        # Encode the frame as JPEG
        ret, buffer = cv2.imencode('.jpg', frame)
        if not ret:
            print("Error: Failed to encode frame.")
            continue

        frame_bytes = buffer.tobytes()

        # Yield the frame in bytes for streaming
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

# --- Flask Routes ---
@app.route('/')
def index():
    """Render the main HTML page."""
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    """
    Endpoint to stream video frames.
    Uses multipart/x-mixed-replace for MJPEG streaming.
    """
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/analytics')
def analytics():
    """
    Endpoint to provide real-time analytics data.
    """
    # In a real application, you might fetch these from a more robust
    # analytics processing pipeline or a database.
    return jsonify({
        'face_count': global_face_count,
        'sleeping_status': global_sleeping_status,
        'focus_score': round(global_focus_score, 2),
        'unauthorized_activity': global_unauthorized_activity_status,
        'copy_attempt': global_copy_attempt_status,
        'proctoring_alert': global_proctoring_alert_status
    })

# --- Main execution block ---
if __name__ == '__main__':
    # Ensure the camera is released when the app stops
    import atexit
    atexit.register(lambda: camera.release())

    print(f"Flask app starting. Access at http://127.0.0.1:5000/")
    print("Make sure 'haarcascade_frontalface_default.xml' is in the same directory.")
    app.run(host='0.0.0.0', port=5000, debug=True)
