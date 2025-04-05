import base64
import io
import cv2
import numpy as np
import mediapipe as mp
from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
from PIL import Image

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Set up MediaPipe
mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose
# Create a global pose instance (for reuse across requests)
pose = mp_pose.Pose(min_detection_confidence=0.6, min_tracking_confidence=0.6)

# --- Utility Functions ---
def calculate_angle(a, b, c):
    a2d = np.array(a[:2])
    b2d = np.array(b[:2])
    c2d = np.array(c[:2])
    ba = a2d - b2d
    bc = c2d - b2d
    cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
    angle = np.arccos(np.clip(cosine_angle, -1.0, 1.0))
    return np.degrees(angle)

def calculate_midpoint(a, b):
    return [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2, (a[2] + b[2]) / 2]

def get_landmark_point(landmark, frame):
    # Convert normalized landmark to pixel coordinates based on frame dimensions
    return [int(landmark.x * frame.shape[1]),
            int(landmark.y * frame.shape[0]),
            landmark.z]

@app.route('/analyze', methods=['POST'])
@cross_origin()
def analyze():
    data = request.get_json()
    if not data or 'image' not in data:
        return jsonify({"error": "No image provided"}), 400

    # Extract base64 string and decode
    image_base64 = data['image']
    if image_base64.startswith("data:image"):
        image_base64 = image_base64.split(",")[1]
    try:
        image_data = base64.b64decode(image_base64)
        np_img = np.frombuffer(image_data, np.uint8)
        frame = cv2.imdecode(np_img, cv2.IMREAD_COLOR)
    except Exception as e:
        return jsonify({"error": "Invalid image data", "details": str(e)}), 400

    # Convert the frame to RGB and process with MediaPipe
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    rgb_frame.flags.writeable = False
    results = pose.process(rgb_frame)
    rgb_frame.flags.writeable = True
    processed_frame = cv2.cvtColor(rgb_frame, cv2.COLOR_RGB2BGR)

    # Initialize feedback
    feedback = "No pose detected."
    if results.pose_landmarks:
        landmarks = results.pose_landmarks.landmark

        # Get some key landmarks (modify as needed)
        shoulderL = get_landmark_point(landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value], frame)
        shoulderR = get_landmark_point(landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value], frame)
        hipL = get_landmark_point(landmarks[mp_pose.PoseLandmark.LEFT_HIP.value], frame)
        hipR = get_landmark_point(landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value], frame)
        kneeL = get_landmark_point(landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value], frame)
        kneeR = get_landmark_point(landmarks[mp_pose.PoseLandmark.RIGHT_KNEE.value], frame)
        
        # Calculate midpoint and back angle
        midpointShoulder = calculate_midpoint(shoulderL, shoulderR)
        midpointHips = calculate_midpoint(hipL, hipR)
        # For simplicity, we use hips and shoulders to estimate back posture
        angleBack = calculate_angle(midpointShoulder, midpointHips, hipL)  # Example calculation
        
        # Generate simple feedback based on back angle threshold
        if angleBack < 150:
            feedback = "Lean forward too much"
        else:
            feedback = "Good form detected!"

        # Overlay feedback text on the frame
        cv2.putText(processed_frame, feedback, (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        # Draw pose landmarks on the frame
        mp_drawing.draw_landmarks(processed_frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)

    # Encode processed_frame to JPEG and then to base64 for the browser
    retval, buffer = cv2.imencode('.jpg', processed_frame)
    jpg_as_text = base64.b64encode(buffer).decode('utf-8')
    annotated_image = f"data:image/jpeg;base64,{jpg_as_text}"

    return jsonify({
        "feedback": feedback,
        "annotated_image": annotated_image
    })

if __name__ == '__main__':
    app.run(host="127.0.0.1", port=5000, debug=True)
