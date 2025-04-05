import base64
import cv2
import numpy as np
import mediapipe as mp
import os
import time
import threading
import queue
from pyneuphonic import Neuphonic, TTSConfig
from pyneuphonic.player import AudioPlayer
import dotenv 
from flask import Flask, request, jsonify
from flask_cors import CORS

dotenv.load_dotenv()

app = Flask(__name__)
CORS(app)

# MediaPipe setup
mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(min_detection_confidence=0.6, min_tracking_confidence=0.6)

# Neuphonic TTS setup
client = Neuphonic(api_key=os.environ.get('NEUPHONIC_API_KEY'))
sse = client.tts.SSEClient()
tts_config = TTSConfig(lang_code='en', sampling_rate=22050)

# Audio queue and threading
audio_queue = queue.Queue()
last_audio_time = 0
AUDIO_COOLDOWN = 3
reached_bottom = False
perfect_form_flag = False

def audio_worker():
    while True:
        message = audio_queue.get()
        if message is None:
            break
        try:
            with AudioPlayer(sampling_rate=22050) as player:
                response = sse.send(message, tts_config=tts_config)
                player.play(response)
        except Exception as e:
            print(f"Audio error: {e}")
        audio_queue.task_done()

audio_thread = threading.Thread(target=audio_worker, daemon=True)
audio_thread.start()

# Utility functions
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
    return [(a[0] + b[0])/2, (a[1] + b[1])/2, (a[2] + b[2])/2]

def get_landmark_point(landmark, frame):
    return [int(landmark.x * frame.shape[1]),
            int(landmark.y * frame.shape[0]),
            landmark.z]

@app.route('/analyze', methods=['POST'])
def analyze():
    global last_audio_time, reached_bottom, perfect_form_flag
    
    data = request.get_json()
    if not data or 'image' not in data:
        return jsonify({"error": "No image provided"}), 400

    try:
        current_exercise = data["exercise"]
        image_base64 = data['image'].split(",")[1] if data['image'].startswith("data:image") else data['image']
        frame = cv2.imdecode(np.frombuffer(base64.b64decode(image_base64), np.uint8), cv2.IMREAD_COLOR)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(rgb_frame)
        processed_frame = cv2.cvtColor(rgb_frame, cv2.COLOR_RGB2BGR)
        feedback = "No pose detected"
        current_time = time.time()

        if current_exercise == "squat":

            if results.pose_landmarks:
                landmarks = results.pose_landmarks.landmark
                
                # Get landmarks
                shoulderL = get_landmark_point(landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value], frame)
                shoulderR = get_landmark_point(landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value], frame)
                hipL = get_landmark_point(landmarks[mp_pose.PoseLandmark.LEFT_HIP.value], frame)
                hipR = get_landmark_point(landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value], frame)
                kneeL = get_landmark_point(landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value], frame)
                kneeR = get_landmark_point(landmarks[mp_pose.PoseLandmark.RIGHT_KNEE.value], frame)
                ankleL = get_landmark_point(landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value], frame)
                ankleR = get_landmark_point(landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE.value], frame)

                # Calculate angles and midpoints
                angleKneeL = int(calculate_angle(hipL, kneeL, ankleL))
                angleKneeR = int(calculate_angle(hipR, kneeR, ankleR))
                midpointShoulder = calculate_midpoint(shoulderL, shoulderR)
                midpointHips = calculate_midpoint(hipL, hipR)
                midpointKnees = calculate_midpoint(kneeL, kneeR)
                angleBack = calculate_angle(midpointShoulder, midpointHips, midpointKnees)

                # Squat parameters
                knee_valgus_threshold = 100
                back_lean_threshold = 65
                depth_threshold = 0.75
                depth_left = hipL[1] > kneeL[1] * depth_threshold
                depth_right = hipR[1] > kneeR[1] * depth_threshold
                current_depth_met = depth_left and depth_right
                knee_valgus_left = (kneeL[0] - ankleL[0]) > knee_valgus_threshold
                knee_valgus_right = (ankleR[0] - kneeR[0]) > knee_valgus_threshold

                # Posture checks
                feedback_given = False
                perfect_form = False

                if not current_depth_met:
                    if (current_time - last_audio_time) > AUDIO_COOLDOWN:
                        audio_queue.put("Go lower")
                        last_audio_time = current_time
                        cv2.putText(processed_frame, "Go Lower!", (10, 120), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                        feedback_given = True
                        perfect_form_flag = False
                elif angleBack < back_lean_threshold:
                    if (current_time - last_audio_time) > AUDIO_COOLDOWN:
                        audio_queue.put("Lean forward too much")
                        last_audio_time = current_time
                        cv2.putText(processed_frame, "Lean Forward Too Much!", (10, 90), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                        feedback_given = True
                elif knee_valgus_left:
                    if (current_time - last_audio_time) > AUDIO_COOLDOWN:
                        audio_queue.put("Left knee in")
                        last_audio_time = current_time
                        cv2.putText(processed_frame, "Left Knee In!", 
                                (int(kneeL[0] - 50), int(kneeL[1])),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                        feedback_given = True
                elif knee_valgus_right:
                    if (current_time - last_audio_time) > AUDIO_COOLDOWN:
                        audio_queue.put("Right knee in")
                        last_audio_time = current_time
                        cv2.putText(processed_frame, "Right Knee In!", 
                                (int(kneeR[0] - 50), int(kneeR[1])),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                        feedback_given = True
                else:
                    perfect_form = True

                if perfect_form:
                    if current_depth_met:
                        if not perfect_form_flag:
                            audio_queue.put("Good form, go up")
                            last_audio_time = current_time
                            cv2.putText(processed_frame, "Perfect! Go Up!", (10, 60), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                            perfect_form_flag = True
                    else:
                        perfect_form_flag = False

                # Draw angles and landmarks
                cv2.putText(processed_frame, f'{angleKneeL}', 
                        (int(kneeL[0] - 30), int(kneeL[1] - 10)),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                cv2.putText(processed_frame, f'{angleKneeR}', 
                        (int(kneeR[0] - 30), int(kneeR[1] - 10)),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                cv2.putText(processed_frame, f'{int(angleBack)}', 
                        (int(midpointHips[0] - 30), int(midpointHips[1] - 10)),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                
                mp_drawing.draw_landmarks(processed_frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
                feedback = "Analysis complete"

            # Encode and return image
            _, buffer = cv2.imencode('.jpg', processed_frame)
            return jsonify({
                "feedback": feedback,
                "annotated_image": f"data:image/jpeg;base64,{base64.b64encode(buffer).decode()}"
            })
        elif current_exercise == "pushup":
            pass


    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host="127.0.0.1", port=5000)