import mediapipe as mp
import cv2
import numpy as np
import os
import time
import threading
import queue
from pyneuphonic import Neuphonic, TTSConfig
from pyneuphonic.player import AudioPlayer
import dotenv 

dotenv.load_dotenv()

# Set up for mediapipe
mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose

# Neuphonic TTS setup
client = Neuphonic(api_key=os.environ.get('NEUPHONIC_API_KEY'))
sse = client.tts.SSEClient()
tts_config = TTSConfig(lang_code='en', sampling_rate=22050)

# Audio queue and threading setup
audio_queue = queue.Queue()
last_audio_time = 0
AUDIO_COOLDOWN = 3  # Seconds between audio cues

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

# --- Utility Functions ---
def calculate_angle(a, b, c):
    a = np.array(a[:2])
    b = np.array(b[:2])
    c = np.array(c[:2])
    
    radians = np.arctan2(c[1]-b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
    angle = np.abs(np.degrees(radians))
    
    if angle > 180:
        angle = 360 - angle
        
    return angle

def get_landmark_point(landmark, frame):
    return [landmark.x * frame.shape[1],
            landmark.y * frame.shape[0],
            landmark.z]

# Bicep Curl Variables
rep_count = 0
stage = "down"
BACK_LEAN_THRESHOLD = 15  # Degrees of allowable forward lean
ELBOW_RANGE = {          # Elbow angle thresholds
    'down': 160,
    'up': 60
}

# --- Main loop for openCV ---
cap = cv2.VideoCapture(0)

try:
    with mp_pose.Pose(min_detection_confidence=0.6, min_tracking_confidence=0.6) as pose:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image.flags.writeable = False
            results = pose.process(image)
            image.flags.writeable = True
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

            try:
                landmarks = results.pose_landmarks.landmark

                # Get relevant landmarks
                shoulder = get_landmark_point(landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER], frame)
                elbow = get_landmark_point(landmarks[mp_pose.PoseLandmark.LEFT_ELBOW], frame)
                wrist = get_landmark_point(landmarks[mp_pose.PoseLandmark.LEFT_WRIST], frame)
                hip = get_landmark_point(landmarks[mp_pose.PoseLandmark.LEFT_HIP], frame)

                # Calculate angles
                elbow_angle = int(calculate_angle(shoulder, elbow, wrist))
                
                # Back lean calculation (shoulder to hip vertical alignment)
                shoulder_hip_horizontal_diff = abs(shoulder[0] - hip[0])
                back_lean = shoulder_hip_horizontal_diff / frame.shape[1] * 100  # Percentage of frame width

                # Bicep curl rep counter logic
                if elbow_angle > ELBOW_RANGE['down']:
                    stage = "down"
                elif elbow_angle < ELBOW_RANGE['up'] and stage == "down":
                    stage = "up"
                    rep_count += 1
                    audio_queue.put(f"Rep {rep_count} counted")

                # Posture feedback
                current_time = time.time()
                feedback_given = False
                
                # Elbow range feedback
                if stage == "up" and elbow_angle > ELBOW_RANGE['up'] + 20:
                    if (current_time - last_audio_time) > AUDIO_COOLDOWN:
                        audio_queue.put("Lift higher")
                        last_audio_time = current_time
                        cv2.putText(image, "Lift Higher!", (10, 60), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                        feedback_given = True
                
                # Back lean feedback
                if back_lean > BACK_LEAN_THRESHOLD:
                    if (current_time - last_audio_time) > AUDIO_COOLDOWN and not feedback_given:
                        audio_queue.put("Keep your back straight")
                        last_audio_time = current_time
                        cv2.putText(image, "Keep Back Straight!", (10, 90), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                        feedback_given = True

                # Visual feedback
                cv2.putText(image, f'Elbow: {elbow_angle}', (10, 30), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                cv2.putText(image, f'Reps: {rep_count}', (10, 120), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                cv2.putText(image, f'Back Lean: {int(back_lean)}%', (10, 150), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
                cv2.putText(image, f'{back_lean}', 
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)

            except Exception as e:
                if str(e) == "'NoneType' object has no attribute 'landmark'":
                    pass
                else:
                    print("Error processing pose:", e)

            mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
            cv2.imshow("Bicep Curl Form Check", image)
            
            if cv2.waitKey(10) & 0xFF == ord("q"):
                break

finally:
    # Cleanup process
    print("Shutting down...")
    
    # Clear audio queue
    while not audio_queue.empty():
        try:
            audio_queue.get_nowait()
            audio_queue.task_done()
        except queue.Empty:
            break
    
    # Signal audio thread to exit
    audio_queue.put(None)
    
    # Wait for audio thread to finish
    audio_thread.join(timeout=2)
    
    # Release resources
    if cap.isOpened():
        cap.release()
    cv2.destroyAllWindows()