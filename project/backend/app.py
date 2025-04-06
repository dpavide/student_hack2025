import base64
import cv2
import numpy as np
import mediapipe as mp
import os
import time
import threading
import queue
from flask import Flask, request, jsonify
from flask_cors import CORS
import dotenv 
from datetime import datetime

dotenv.load_dotenv()

# Own file imports
from squat_processor import process_squat
from push_up_processor import process_pushup
from bicep_curl_processor import process_bicep_curl

app = Flask(__name__)
CORS(app)

# Global variable to hold latest landmark data for AR overlay
latest_landmark_data = None

# MediaPipe setup
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(min_detection_confidence=0.6, min_tracking_confidence=0.6)

# Neuphonic TTS setup
from pyneuphonic import Neuphonic, TTSConfig
from pyneuphonic.player import AudioPlayer
client = Neuphonic(api_key=os.environ.get('NEUPHONIC_API_KEY'))
sse = client.tts.SSEClient()
tts_config = TTSConfig(lang_code='en', sampling_rate=22050)

# Audio queue and threading
audio_queue = queue.Queue()
last_audio_time = 0
AUDIO_COOLDOWN = 3
perfect_form_flag = False
pushup_phase = "down"  # Initialize pushup_phase for pushup analysis
bicep_phase = "down"

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

@app.route('/latest-landmarks', methods=['GET'])
def latest_landmarks():
    if latest_landmark_data:
        return jsonify(latest_landmark_data), 200
    else:
        return jsonify({"error": "No landmark data available"}), 404

@app.route('/analyze', methods=['POST'])
def analyze():
    global latest_landmark_data, last_audio_time, perfect_form_flag, pushup_phase, bicep_phase

    data = request.get_json()
    if not data or 'image' not in data:
        return jsonify({"error": "No image provided"}), 400

    try:
        current_exercise = data.get("exercise", "squat").lower()
        image_data_str = data['image']
        if image_data_str.startswith("data:image"):
            image_data_str = image_data_str.split(",")[1]
        frame = cv2.imdecode(np.frombuffer(base64.b64decode(image_data_str), np.uint8), cv2.IMREAD_COLOR)
        current_time = time.time()

        # Helper function to extract landmark coordinates in normalized [0,1] space.
        def extract_landmarks(frame, results, mp_pose):
            if not results.pose_landmarks:
                return {"shoulders": [], "hips": [], "knees": []}
            landmarks = results.pose_landmarks.landmark
            def get_point(landmark):
                return [landmark.x, landmark.y, landmark.z]
            shoulders = [get_point(landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER]),
                         get_point(landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER])]
            hips = [get_point(landmarks[mp_pose.PoseLandmark.LEFT_HIP]),
                    get_point(landmarks[mp_pose.PoseLandmark.RIGHT_HIP])]
            knees = [get_point(landmarks[mp_pose.PoseLandmark.LEFT_KNEE]),
                     get_point(landmarks[mp_pose.PoseLandmark.RIGHT_KNEE])]
            return {"shoulders": shoulders, "hips": hips, "knees": knees}

        if current_exercise == "squat":
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = pose.process(rgb_frame)
            feedback, processed_frame, perfect_form_flag, last_audio_time = process_squat(
                frame, results, mp_pose,
                last_audio_time, audio_queue, perfect_form_flag, current_time,
                AUDIO_COOLDOWN
            )
            # Extract landmarks for AR overlay
            if results.pose_landmarks:
                landmarks = results.pose_landmarks.landmark
                # Extract some landmarks – adjust indices and scaling as needed.
                shoulders = [
                {"x": landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER].x, "y": landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER].y, "z": landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER].z},
                {"x": landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER].x, "y": landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER].y, "z": landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER].z}
                ]
                hips = [
                {"x": landmarks[mp_pose.PoseLandmark.LEFT_HIP].x, "y": landmarks[mp_pose.PoseLandmark.LEFT_HIP].y, "z": landmarks[mp_pose.PoseLandmark.LEFT_HIP].z},
                {"x": landmarks[mp_pose.PoseLandmark.RIGHT_HIP].x, "y": landmarks[mp_pose.PoseLandmark.RIGHT_HIP].y, "z": landmarks[mp_pose.PoseLandmark.RIGHT_HIP].z}
                ]
                knees = [
                {"x": landmarks[mp_pose.PoseLandmark.LEFT_KNEE].x, "y": landmarks[mp_pose.PoseLandmark.LEFT_KNEE].y, "z": landmarks[mp_pose.PoseLandmark.LEFT_KNEE].z},
                {"x": landmarks[mp_pose.PoseLandmark.RIGHT_KNEE].x, "y": landmarks[mp_pose.PoseLandmark.RIGHT_KNEE].y, "z": landmarks[mp_pose.PoseLandmark.RIGHT_KNEE].z}
                ]
                latest_landmark_data = {
                    "timestamp": datetime.now().isoformat(),
                    "feedback": feedback,
                    "coordinates": {
                        "shoulders": shoulders,
                        "hips": hips,
                        "knees": knees
                    }
                }

            _, buffer = cv2.imencode('.jpg', processed_frame)
            return jsonify({
                "feedback": feedback,
                "annotated_image": f"data:image/jpeg;base64,{base64.b64encode(buffer).decode()}"
            })
        
        elif current_exercise == "pushup":
            global pushup_phase  # Declare as global so we can update it
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = pose.process(rgb_frame)
            feedback, processed_frame, pushup_phase, last_audio_time = process_pushup(
                frame, results, mp_pose,
                last_audio_time, audio_queue, pushup_phase, current_time,
                AUDIO_COOLDOWN
            )
            # Optionally update latest_landmark_data with pushup landmarks
            
            if results.pose_landmarks:
                landmarks = results.pose_landmarks.landmark
                # Extract some landmarks – adjust indices and scaling as needed.
                shoulders = [
                {"x": landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER].x, "y": landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER].y, "z": landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER].z},
                {"x": landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER].x, "y": landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER].y, "z": landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER].z}
                ]
                hips = [
                {"x": landmarks[mp_pose.PoseLandmark.LEFT_HIP].x, "y": landmarks[mp_pose.PoseLandmark.LEFT_HIP].y, "z": landmarks[mp_pose.PoseLandmark.LEFT_HIP].z},
                {"x": landmarks[mp_pose.PoseLandmark.RIGHT_HIP].x, "y": landmarks[mp_pose.PoseLandmark.RIGHT_HIP].y, "z": landmarks[mp_pose.PoseLandmark.RIGHT_HIP].z}
                ]
                knees = [
                {"x": landmarks[mp_pose.PoseLandmark.LEFT_KNEE].x, "y": landmarks[mp_pose.PoseLandmark.LEFT_KNEE].y, "z": landmarks[mp_pose.PoseLandmark.LEFT_KNEE].z},
                {"x": landmarks[mp_pose.PoseLandmark.RIGHT_KNEE].x, "y": landmarks[mp_pose.PoseLandmark.RIGHT_KNEE].y, "z": landmarks[mp_pose.PoseLandmark.RIGHT_KNEE].z}
                ]
                latest_landmark_data = {
                    "timestamp": datetime.now().isoformat(),
                    "feedback": feedback,
                    "coordinates": {
                        "shoulders": shoulders,
                        "hips": hips,
                        "knees": knees
                    }
                }

            _, buffer = cv2.imencode('.jpg', processed_frame)
            return jsonify({
                "feedback": feedback,
                "annotated_image": f"data:image/jpeg;base64,{base64.b64encode(buffer).decode()}"
            })
        
        elif current_exercise == "bicep":
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = pose.process(rgb_frame)
            feedback, processed_frame, bicep_phase, last_audio_time = process_bicep_curl(
                frame, results, mp_pose,
                last_audio_time, audio_queue, bicep_phase, current_time,
                AUDIO_COOLDOWN
            )
            # Update landmark data for AR if needed
            if results.pose_landmarks:
                landmarks = results.pose_landmarks.landmark
                # Extract some landmarks – adjust indices and scaling as needed.
                shoulders = [
                {"x": landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER].x, "y": landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER].y, "z": landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER].z},
                {"x": landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER].x, "y": landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER].y, "z": landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER].z}
                ]
                hips = [
                {"x": landmarks[mp_pose.PoseLandmark.LEFT_HIP].x, "y": landmarks[mp_pose.PoseLandmark.LEFT_HIP].y, "z": landmarks[mp_pose.PoseLandmark.LEFT_HIP].z},
                {"x": landmarks[mp_pose.PoseLandmark.RIGHT_HIP].x, "y": landmarks[mp_pose.PoseLandmark.RIGHT_HIP].y, "z": landmarks[mp_pose.PoseLandmark.RIGHT_HIP].z}
                ]
                knees = [
                {"x": landmarks[mp_pose.PoseLandmark.LEFT_KNEE].x, "y": landmarks[mp_pose.PoseLandmark.LEFT_KNEE].y, "z": landmarks[mp_pose.PoseLandmark.LEFT_KNEE].z},
                {"x": landmarks[mp_pose.PoseLandmark.RIGHT_KNEE].x, "y": landmarks[mp_pose.PoseLandmark.RIGHT_KNEE].y, "z": landmarks[mp_pose.PoseLandmark.RIGHT_KNEE].z}
                ]
                latest_landmark_data = {
                    "timestamp": datetime.now().isoformat(),
                    "feedback": feedback,
                    "coordinates": {
                        "shoulders": shoulders,
                        "hips": hips,
                        "knees": knees
                    }
                }

            _, buffer = cv2.imencode('.jpg', processed_frame)
            return jsonify({
                "feedback": feedback,
                "annotated_image": f"data:image/jpeg;base64,{base64.b64encode(buffer).decode()}"
            })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host="127.0.0.1", port=5000)
