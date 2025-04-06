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

dotenv.load_dotenv()
from squat_processor import process_squat

app = Flask(__name__)
CORS(app)

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

@app.route('/analyze', methods=['POST'])
def analyze():
    global last_audio_time, perfect_form_flag

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

        if current_exercise == "squat":
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = pose.process(rgb_frame)
            feedback, processed_frame, perfect_form_flag, last_audio_time = process_squat(
                frame, results, mp_pose,
                last_audio_time, audio_queue, perfect_form_flag, current_time,
                AUDIO_COOLDOWN
            )
            _, buffer = cv2.imencode('.jpg', processed_frame)
            return jsonify({
                "feedback": feedback,
                "annotated_image": f"data:image/jpeg;base64,{base64.b64encode(buffer).decode()}"
            })

        elif current_exercise == "pushup":
            # Dummy processing remains same
            return jsonify({"feedback": "Dummy pushup analysis", "annotated_image": ""})

        else:
            return jsonify({"error": "Unknown exercise type"}), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host="127.0.0.1", port=5000)
