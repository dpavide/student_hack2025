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
AUDIO_COOLDOWN = 1  # Seconds between audio cues

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

def get_landmark_point(landmark):
    return [int(landmark.x * frame.shape[1]),
            int(landmark.y * frame.shape[0]),
            landmark.z]

# --- Main loop for openCV ---
cap = cv2.VideoCapture(0)

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

            # Get landmarks
            shoulderL = get_landmark_point(landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER])
            shoulderR = get_landmark_point(landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER])
            hipL = get_landmark_point(landmarks[mp_pose.PoseLandmark.LEFT_HIP])
            hipR = get_landmark_point(landmarks[mp_pose.PoseLandmark.RIGHT_HIP])
            kneeL = get_landmark_point(landmarks[mp_pose.PoseLandmark.LEFT_KNEE])
            kneeR = get_landmark_point(landmarks[mp_pose.PoseLandmark.RIGHT_KNEE])
            ankleL = get_landmark_point(landmarks[mp_pose.PoseLandmark.LEFT_ANKLE])
            ankleR = get_landmark_point(landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE])
            heelL = get_landmark_point(landmarks[mp_pose.PoseLandmark.LEFT_HEEL])
            heelR = get_landmark_point(landmarks[mp_pose.PoseLandmark.RIGHT_HEEL])
            footIndexL = get_landmark_point(landmarks[mp_pose.PoseLandmark.LEFT_FOOT_INDEX])
            footIndexR = get_landmark_point(landmarks[mp_pose.PoseLandmark.RIGHT_FOOT_INDEX])

            # Calculate angles
            angleKneeL = int(calculate_angle(hipL, kneeL, ankleL))
            angleKneeR = int(calculate_angle(hipR, kneeR, ankleR))
            midpointShoulder = calculate_midpoint(shoulderL, shoulderR)
            midpointHips = calculate_midpoint(hipL, hipR)
            midpointKnees = calculate_midpoint(kneeL, kneeR)
            angleBack = calculate_angle(midpointShoulder, midpointHips, midpointKnees)

            # Squat analysis parameters
            current_time = time.time()
            knee_valgus_threshold = 20
            back_lean_threshold = 150
            depth_threshold = 0.9
            heel_lift_threshold = 30

            # Posture checks with audio cooldown
            if angleBack < back_lean_threshold and (current_time - last_audio_time) > AUDIO_COOLDOWN:
                audio_queue.put("Lean forward too much")
                last_audio_time = current_time
                cv2.putText(image, "Lean Forward Too Much!", (10, 90), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

            depth_left = hipL[1] > kneeL[1] * depth_threshold
            depth_right = hipR[1] > kneeR[1] * depth_threshold
            if not (depth_left and depth_right) and (current_time - last_audio_time) > AUDIO_COOLDOWN:
                audio_queue.put("Go lower")
                last_audio_time = current_time
                cv2.putText(image, "Go Lower!", (10, 120), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

            if abs(heelL[1] - footIndexL[1]) > heel_lift_threshold and (current_time - last_audio_time) > AUDIO_COOLDOWN:
                audio_queue.put("Left heel up")
                last_audio_time = current_time
                cv2.putText(image, "Left Heel Up!", (10, 150), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

            if abs(heelR[1] - footIndexR[1]) > heel_lift_threshold and (current_time - last_audio_time) > AUDIO_COOLDOWN:
                audio_queue.put("Right heel up")
                last_audio_time = current_time
                cv2.putText(image, "Right Heel Up!", (10, 180), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

            knee_valgus_left = (kneeL[0] - ankleL[0]) > knee_valgus_threshold
            knee_valgus_right = (ankleR[0] - kneeR[0]) > knee_valgus_threshold
            
            if knee_valgus_left and (current_time - last_audio_time) > AUDIO_COOLDOWN:
                audio_queue.put("Left knee in")
                last_audio_time = current_time
                cv2.putText(image, "Left Knee In!", 
                            (int(kneeL[0] - 50), int(kneeL[1])),  # Fixed coordinates
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

            if knee_valgus_right and (current_time - last_audio_time) > AUDIO_COOLDOWN:
                audio_queue.put("Right knee in")
                last_audio_time = current_time
                cv2.putText(image, "Right Knee In!", 
                            (int(kneeR[0] - 50), int(kneeR[1])),  # Fixed coordinates
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

            # Display angles with fixed coordinates
            cv2.putText(image, f'{angleKneeL}', 
                        (int(kneeL[0] - 30), int(kneeL[1] - 10)),  # Convert to int
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
            
            cv2.putText(image, f'{angleKneeR}', 
                        (int(kneeR[0] - 30), int(kneeR[1] - 10)),  # Convert to int
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
            
            cv2.putText(image, f'{int(angleBack)}', 
                        (int(midpointHips[0] - 30), int(midpointHips[1] - 10)),  # Convert to int
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)

        except Exception as e:
            if str(e) == "'NoneType' object has no attribute 'landmark'":
                pass
            else:
                print("Error processing pose:", e)

        mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
        cv2.imshow("Body recognition", image)
        
        if cv2.waitKey(10) & 0xFF == ord("q"):
            break

# Cleanup
audio_queue.put(None)
audio_thread.join()
cap.release()
cv2.destroyAllWindows()