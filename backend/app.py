import cv2
import time
from flask import Flask, Response, jsonify, render_template
import numpy as np
import random

# Import dlib for face detection and landmark prediction
import dlib
from scipy.spatial import distance as dist # For calculating Euclidean distance for EAR/MAR

app = Flask(__name__)

# --- Configuration ---
# Use 0 for default webcam, or a video file path
VIDEO_SOURCE = 0
# Interval for updating analytics (in seconds)
ANALYTICS_UPDATE_INTERVAL = 1 # Faster UI updates

# --- AI Detection Thresholds (Using real landmark data) ---
EYE_AR_THRESH = 0.25 # Threshold for eye aspect ratio (drowsiness)
EYE_AR_CONSEC_FRAMES = 10 # Number of consecutive frames eye must be below threshold
MOUTH_AR_THRESH = 0.7 # Threshold for mouth aspect ratio (yawning)
MOUTH_AR_CONSEC_FRAMES = 10 # Number of consecutive frames mouth must be above threshold
# Head pose thresholds (in arbitrary units/degrees for simplified estimation)
HEAD_POSE_YAW_THRESH = 15 # Horizontal head rotation deviation threshold
HEAD_POSE_PITCH_THRESH = 15 # Vertical head rotation deviation threshold
GAZE_AWAY_CONSEC_FRAMES = 30 # Number of consecutive frames gaze/head pose is away
ABSENCE_TIME_THRESHOLD = 5 # Seconds of no face to trigger absent status

# --- Global Variables for Analytics ---
global_face_count = 0
global_sleeping_status = "No person detected"
global_focus_score = 0.0
global_unauthorized_activity_status = "None Detected"
global_copy_attempt_status = "None Detected"
global_proctoring_alert_status = "No Violations"
global_current_alert_type = None # New: Holds the type of alert for frontend

# --- AI Detection State Variables ---
# For Drowsiness/Yawn Detection
COUNTER = 0 # Frame counter for eye aspect ratio below threshold
YAWN_COUNTER = 0 # Frame counter for mouth aspect ratio above threshold
# For Gaze/Head Pose Detection
HEAD_POSE_AWAY_COUNTER = 0 # Frame counter for head pose deviation

# Timestamp of the last person detected
last_person_detected_time = time.time()

# --- Initialize dlib's face detector (HOG-based) and facial landmark predictor ---
detector = dlib.get_frontal_face_detector()
# You MUST download shape_predictor_68_face_landmarks.dat and place it in the 'backend' directory.
# Download from: http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2
try:
    predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")
    print("dlib face detector and shape predictor initialized successfully.")
except Exception as e:
    print(f"Error loading dlib shape predictor: {e}")
    print("CRITICAL: Please download 'shape_predictor_68_face_landmarks.dat' from http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2, extract it, and place it in the same directory as app.py.")
    predictor = None # Set to None to handle errors gracefully

# --- Helper functions for Eye and Mouth Aspect Ratios ---
def eye_aspect_ratio(eye):
    # Compute the Euclidean distances between the two sets of vertical eye landmarks
    A = dist.euclidean(eye[1], eye[5])
    B = dist.euclidean(eye[2], eye[4])
    # Compute the Euclidean distance between the horizontal eye landmark
    C = dist.euclidean(eye[0], eye[3])
    # Compute the eye aspect ratio
    ear = (A + B) / (2.0 * C)
    return ear

def mouth_aspect_ratio(mouth):
    # Compute the Euclidean distances between the two sets of vertical mouth landmarks (51, 59) and (53, 57)
    A = dist.euclidean(mouth[2], mouth[10]) # Points 51 and 59
    B = dist.euclidean(mouth[4], mouth[8])  # Points 53 and 57
    # Compute the Euclidean distance between the horizontal mouth landmarks (48, 54)
    C = dist.euclidean(mouth[0], mouth[6]) # Points 48 and 54
    # Compute the mouth aspect ratio
    mar = (A + B) / (2.0 * C)
    return mar

# --- Video Capture Initialization ---
print(f"Attempting to open camera source: {VIDEO_SOURCE}")
camera = cv2.VideoCapture(VIDEO_SOURCE)
if not camera.isOpened():
    print(f"Error: Could not open video source {VIDEO_SOURCE}. Is it in use by another app or not connected? Please check permissions.")
    exit() # Exit if camera cannot be opened
else:
    print(f"Successfully opened video source {VIDEO_SOURCE}.")

# --- AI Detection Logic (Intelligent AI with dlib) ---
def perform_ai_detection(frame):
    """
    Performs AI-based detection for sleeping, focus, unauthorized activity,
    and copy attempts using dlib facial landmarks.
    Returns a string indicating the type of alert, or None.
    """
    global global_face_count, global_sleeping_status, global_focus_score, \
           global_unauthorized_activity_status, global_copy_attempt_status, \
           global_proctoring_alert_status, last_person_detected_time, \
           COUNTER, YAWN_COUNTER, HEAD_POSE_AWAY_COUNTER

    current_time = time.time()
    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    current_frame_alert_type = None # Local variable to hold alert for this frame

    # Detect faces in the grayscale frame using dlib's HOG detector
    rects = detector(gray_frame, 0) # 0 means no upsampling

    global_face_count = len(rects)

    # Variables to store data for the primary face for detailed analysis and drawing
    primary_rect = None
    primary_landmarks = None
    
    if global_face_count > 0:
        last_person_detected_time = current_time
        # Reset non-persistent statuses unless re-triggered in this frame
        global_unauthorized_activity_status = "None Detected"
        global_copy_attempt_status = "None Detected"
        
        # Reset proctoring alert if it was due to absence
        if global_proctoring_alert_status == "Student Absent!":
            global_proctoring_alert_status = "No Violations"

        # Check for multiple people for copy attempt
        if global_face_count > 1:
            global_copy_attempt_status = f"Multiple Persons Detected ({global_face_count})!"
            global_proctoring_alert_status = "Potential Cheating!"
            current_frame_alert_type = "copy_attempt" # Set alert type

        # --- Detailed AI Analysis for the Primary Face ---
        # We focus on the first detected face for detailed EAR/MAR/HeadPose analysis.
        # This part runs only if there's at least one face and predictor is loaded,
        # and if a copy_attempt alert is not already prioritized (optional logic).
        if predictor is not None and len(rects) > 0:
            # We always process the first face for detailed analytics
            primary_rect = rects[0]
            shape = predictor(gray_frame, primary_rect)
            primary_landmarks = np.array([(p.x, p.y) for p in shape.parts()])

            # Extract eye and mouth landmarks (indices from dlib's 68-point model)
            left_eye_indices = [42, 43, 44, 45, 46, 47]
            right_eye_indices = [36, 37, 38, 39, 40, 41]
            mouth_indices = [48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67]

            left_eye = primary_landmarks[left_eye_indices]
            right_eye = primary_landmarks[right_eye_indices]
            mouth = primary_landmarks[mouth_indices]

            # Calculate EAR for both eyes and average
            leftEAR = eye_aspect_ratio(left_eye)
            rightEAR = eye_aspect_ratio(right_eye)
            ear = (leftEAR + rightEAR) / 2.0

            # Calculate MAR for the mouth
            mar = mouth_aspect_ratio(mouth)

            # --- Drowsiness Detection (EAR) ---
            if ear < EYE_AR_THRESH:
                COUNTER += 1
                if COUNTER >= EYE_AR_CONSEC_FRAMES:
                    global_sleeping_status = "Likely Sleeping (Eyes Closed)"
                    global_proctoring_alert_status = "Drowsiness Detected!"
                    if current_frame_alert_type is None: # Only set if no other higher priority alert
                        current_frame_alert_type = "drowsiness" # Set alert type
            else:
                COUNTER = 0 # Reset counter when eyes are open
                # Only set to awake if not already sleeping due to prolonged closure or yawn
                if not ("Likely Sleeping" in global_sleeping_status or "Yawning" in global_sleeping_status):
                    global_sleeping_status = "Awake"

            # --- Yawn Detection (MAR) ---
            if mar > MOUTH_AR_THRESH:
                YAWN_COUNTER += 1
                if YAWN_COUNTER >= MOUTH_AR_CONSEC_FRAMES:
                    global_sleeping_status = "Yawning (AI Detected)"
                    global_proctoring_alert_status = "Yawn Detected - Low Alertness"
                    if current_frame_alert_type is None: # Only set if no other higher priority alert
                        current_frame_alert_type = "yawn" # Set alert type
            else:
                YAWN_COUNTER = 0 # Reset counter when mouth is closed
                # Reset sleeping status if it was only due to yawning and eyes are open
                if global_sleeping_status == "Yawning (AI Detected)" and ear >= EYE_AR_THRESH:
                     global_sleeping_status = "Awake"
            
            # --- Head Pose Estimation (for Gaze/Looking Away) ---
            image_points = np.array([
                primary_landmarks[30], 
                primary_landmarks[8],  
                primary_landmarks[36],
                primary_landmarks[45], 
                primary_landmarks[48], 
                primary_landmarks[54]  
            ], dtype="double")

            # Dummy 3D model points (arbitrary values for a generic face)
            model_points = np.array([
                (0.0, 0.0, 0.0),             
                (0.0, -330.0, -65.0),     
                (-225.0, 170.0, -135.0),     
                (225.0, 170.0, -135.0),      
                (-150.0, -150.0, -125.0),    
                (150.0, -150.0, -125.0)     
            ])

            # Camera internals (Approximations for a generic webcam)
            focal_length = frame.shape[1] 
            center = (frame.shape[1]/2, frame.shape[0]/2)
            camera_matrix = np.array([
                                [focal_length, 0, center[0]],
                                [0, focal_length, center[1]],
                                [0, 0, 1]
                            ], dtype = "double")

            dist_coeffs = np.zeros((4,1)) # Assuming no lens distortion

            # Solve for pose
            (success, rotation_vector, translation_vector) = cv2.solvePnP(model_points, image_points, camera_matrix, dist_coeffs, flags=cv2.SOLVEPNP_ITERATIVE)

            # Get rotation matrix from rotation vector
            rmat, _ = cv2.Rodrigues(rotation_vector)

            # Get angles (Euler angles in degrees)
            angles, _, _, _, _, _ = cv2.RQDecomp3x3(rmat)
            
            # Extract yaw and pitch (in degrees)
            yaw = np.degrees(angles[1])
            pitch = np.degrees(angles[0])

            is_looking_away = False
            if abs(yaw) > HEAD_POSE_YAW_THRESH or abs(pitch) > HEAD_POSE_PITCH_THRESH:
                is_looking_away = True

            if is_looking_away:
                HEAD_POSE_AWAY_COUNTER += 1
                if HEAD_POSE_AWAY_COUNTER >= GAZE_AWAY_CONSEC_FRAMES:
                    global_unauthorized_activity_status = f"Looking Away (Yaw: {round(yaw,1)}deg, Pitch: {round(pitch,1)}deg)"
                    global_proctoring_alert_status = "Attention Diverted!"
                    if current_frame_alert_type is None: 
                        current_frame_alert_type = "gaze_violation" 
            else:
                HEAD_POSE_AWAY_COUNTER = 0
                # Only clear if no other unauthorized activity is set (like multi-person or system violation)
                if not (global_copy_attempt_status != "None Detected" or "System Access" in global_unauthorized_activity_status):
                    global_unauthorized_activity_status = "None Detected"

            # --- Update Focus Score (based on combined real factors) ---
            normalized_ear = min(1.0, ear / EYE_AR_THRESH) if EYE_AR_THRESH > 0 else 1.0
            focus_from_eyes = normalized_ear * 50
            
            normalized_mar = min(1.0, mar / MOUTH_AR_THRESH) if MOUTH_AR_THRESH > 0 else 1.0
            focus_from_mouth = (1.0 - normalized_mar) * 50 # Invert MAR as high MAR means less focus (yawn)
            
            # Penalty for looking away (scales up to 50 if beyond threshold)
            gaze_penalty_factor = min(1.0, HEAD_POSE_AWAY_COUNTER / GAZE_AWAY_CONSEC_FRAMES)
            gaze_penalty = gaze_penalty_factor * 50

            global_focus_score = (focus_from_eyes + focus_from_mouth) - gaze_penalty
            global_focus_score = min(100.0, max(0.0, global_focus_score)) # Cap between 0 and 100

        # --- Draw Rectangles and Landmarks for ALL Detected Faces ---
        for i, rect_draw in enumerate(rects):
            x, y, w, h = rect_draw.left(), rect_draw.top(), rect_draw.width(), rect_draw.height()
            cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
            cv2.putText(frame, f"Person {i+1}", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

           
            if i == 0 and primary_landmarks is not None:
                for (lx, ly) in primary_landmarks:
                    cv2.circle(frame, (lx, ly), 1, (0, 255, 0), -1)

    else: 
        time_since_last_person = current_time - last_person_detected_time
        if time_since_last_person > ABSENCE_TIME_THRESHOLD:
            global_sleeping_status = "No person detected - (Absent)"
            global_proctoring_alert_status = "Student Absent!"
            global_unauthorized_activity_status = "No Person Detected"
            if current_frame_alert_type is None:
                current_frame_alert_type = "absent_violation" 
        else:
            global_sleeping_status = "No person detected" 
            global_unauthorized_activity_status = "None Detected"

        global_focus_score = 0.0
        global_copy_attempt_status = "None Detected"
    
        if global_proctoring_alert_status != "Student Absent!":
            global_proctoring_alert_status = "No Violations"

        # Reset all AI state variables when no face is present
        COUNTER = 0
        YAWN_COUNTER = 0
        HEAD_POSE_AWAY_COUNTER = 0


    # --- Simulate Tab Switching / External Access (conceptual, still random) ---
    if random.random() < 0.0001: # Very low chance per frame
        global_proctoring_alert_status = random.choice([
            "Tab Switched! (Concept)",
            "External App Detected! (Concept)",
            "System Violation! (Concept)"
        ])
        global_unauthorized_activity_status = "System Access Violation (Concept)"
        if current_frame_alert_type is None: 
            current_frame_alert_type = "system_violation" 
            

    return current_frame_alert_type # Return the alert type for the frontend


# --- Generator for Video Streaming ---
def generate_frames():
    """
    Generates MJPEG frames from the webcam, performs AI detection,
    and updates global analytics variables.
    """
    global camera, global_current_alert_type 

    first_frame_read = False

    while True:
        success, frame = camera.read()
        if not success:
            print("Error: Failed to read frame from camera. Attempting to re-open.")
            camera.release() 
            camera = cv2.VideoCapture(VIDEO_SOURCE)
            if not camera.isOpened():
                print(f"Critical Error: Could not re-open video source {VIDEO_SOURCE}. Exiting frame generation.")
                break
            time.sleep(0.1)
            continue

        if not first_frame_read:
            if frame is not None:
                print(f"Successfully read first frame. Frame dimensions: {frame.shape[1]}x{frame.shape[0]} (width x height)")
                first_frame_read = True
            else:
                print("Warning: First frame was None despite success=True. Retrying...")
                continue

        # Perform AI detection and update global variables, capturing the alert type
        global_current_alert_type = perform_ai_detection(frame)

        # Encode the frame as JPEG
        ret, buffer = cv2.imencode('.jpg', frame)
        if not ret:
            print("Error: Failed to encode frame.")
            continue

        frame_bytes = buffer.tobytes()

        # Yield the frame in bytes for streaming
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')


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
    return jsonify({
        'face_count': global_face_count,
        'sleeping_status': global_sleeping_status,
        'focus_score': round(global_focus_score, 2),
        'unauthorized_activity': global_unauthorized_activity_status,
        'copy_attempt': global_copy_attempt_status,
        'proctoring_alert': global_proctoring_alert_status,
        'alert_type': global_current_alert_type 
    })


if __name__ == '__main__':

    import atexit
    atexit.register(lambda: camera.release())

    print(f"Flask app starting. Access at http://127.0.0.1:5000/")
    print("Make sure 'haarcascade_frontalface_default.xml' and 'shape_predictor_68_face_landmarks.dat' are in the same directory.")
    app.run(host='0.0.0.0', port=5000, debug=True)
