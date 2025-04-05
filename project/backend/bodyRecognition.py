import mediapipe as mp
import cv2
import numpy as np
import os
from pyneuphonic import Neuphonic, TTSConfig
from pyneuphonic.player import AudioPlayer
import dotenv 

dotenv.load_dotenv()

# Set up for mediapipe
mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose

# Ensure the API key is set in your environment
client = Neuphonic(api_key=os.environ.get('NEUPHONIC_API_KEY'))

sse = client.tts.SSEClient()

# TTSConfig is a pydantic model so check out the source code for all valid options
tts_config = TTSConfig(
    lang_code='en', # replace the lang_code with the desired language code.
    sampling_rate=22050,
)

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

            def get_landmark_point(landmark):
                return [int(landmark.x * frame.shape[1]),
                        int(landmark.y * frame.shape[0]),
                        landmark.z]
            
            # Arm landmarks
            shoulderL = get_landmark_point(landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER])
            elbowL    = get_landmark_point(landmarks[mp_pose.PoseLandmark.LEFT_ELBOW])
            wristL    = get_landmark_point(landmarks[mp_pose.PoseLandmark.LEFT_WRIST])
            shoulderR = get_landmark_point(landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER])
            elbowR    = get_landmark_point(landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW])
            wristR    = get_landmark_point(landmarks[mp_pose.PoseLandmark.RIGHT_WRIST])

            # Lower body landmarks
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

            # Calculate elbow angles for each arm
            angleElbowL = int(calculate_angle(shoulderL, elbowL, wristL))
            angleElbowR = int(calculate_angle(shoulderR, elbowR, wristR))

            # Calculate knee angles for each leg,
            angleKneeL = int(calculate_angle(hipL, kneeL, ankleL))
            angleKneeR = int(calculate_angle(hipR, kneeR, ankleR))

            # Find midpoints
            midpointShoulder = calculate_midpoint(shoulderL, shoulderR)
            midpointHips = calculate_midpoint(hipL, hipR)
            midpointKnees = calculate_midpoint(kneeL, kneeR)

            # Calculate back angle
            angleBack = calculate_angle(midpointShoulder, midpointHips, midpointKnees)

            # --- Squat analysis check ---

            Status=0

            # Check for knee inward collapse
            knee_valgus_threshold = 20  # Adjust based on testing
            knee_valgus_left = (kneeL[0] - ankleL[0]) > knee_valgus_threshold
            knee_valgus_right = (ankleR[0] - kneeR[0]) > knee_valgus_threshold

            # Back lean
            back_lean_threshold = 150  # Degrees (adjust based on testing)
            if angleBack < back_lean_threshold:
                Status=1
                cv2.putText(image, "Lean Forward Too Much!", (10, 90), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

            # Squat depth
            depth_threshold = 0.9  # Hip below 90% of knee height
            depth_left = (hipL[1] > kneeL[1] * depth_threshold)
            depth_right = (hipR[1] > kneeR[1] * depth_threshold)
            if not (depth_left and depth_right):
                Status=2
                cv2.putText(image, "Go Lower!", (10, 120), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            
            # Heel lift
            heel_lift_threshold = 30  # Pixels (adjust based on testing)
            if abs(heelL[1] - footIndexL[1]) > heel_lift_threshold:
                status=3
                cv2.putText(image, "Left Heel Up!", (10, 150), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            if abs(heelR[1] - footIndexR[1]) > heel_lift_threshold:
                status=4
                cv2.putText(image, "Right Heel Up!", (10, 180), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

            # --- Debug text ---
            cv2.putText(image, f'{angleElbowL}', (elbowL[0] - 30, elbowL[1] - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
            cv2.putText(image, f'{angleElbowR}', (elbowR[0] - 30, elbowR[1] - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
            cv2.putText(image, f'{angleKneeL}', (kneeL[0] - 30, angleKneeL[1] - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
            cv2.putText(image, f'{angleKneeR}', (kneeR[0] - 30, kneeR[1] - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
            cv2.putText(image, f'{angleBack}', (midpointHips[0] - 30, midpointHips[1] - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
            if knee_valgus_left:
                status=5
                cv2.putText(image, "Left Knee In!", (kneeL[0] - 50, kneeL[1]), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            if knee_valgus_right:
                status=6
                cv2.putText(image, "Right Knee In!", (kneeR[0] - 50, kneeR[1]), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        except Exception as e:
            if e == "'NoneType' object has no attribute 'landmark'":
                pass
            else:
                print("Error processing pose:", e)
        
        mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)


        # #Voice feedback
        # if Status == 1:
        #     with AudioPlayer(sampling_rate=22050) as player:
        #         response = sse.send("Leaning Forward too much!", tts_config=tts_config)
        #         player.play(response)
        #     #se.play(tts_config, "Lean Forward Too Much!")
        # elif Status == 2:
        #     with AudioPlayer(sampling_rate=22050) as player:
        #         response = sse.send("Go Lower", tts_config=tts_config)
        #         player.play(response)
        #     #se.play(tts_config, "Go Lower!")
        # elif Status == 3:
        #     with AudioPlayer(sampling_rate=22050) as player:
        #         response = sse.send("Left Heel Up!", tts_config=tts_config)
        #         player.play(response)
        #     #sse.play(tts_config, "Left Heel Up!")
        # elif Status == 4:
        #     with AudioPlayer(sampling_rate=22050) as player:
        #         response = sse.send("Right Heel Up!", tts_config=tts_config)
        #         player.play(response)
        #     #sse.play(tts_config, "Right Heel Up!")
        # elif Status == 5:
        #     with AudioPlayer(sampling_rate=22050) as player:
        #         response = sse.send("Left Knee In!", tts_config=tts_config)
        #         player.play(response)
        #     sse.play(tts_config, "Left Knee In!")
        # elif Status == 6:
        #     with AudioPlayer(sampling_rate=22050) as player:
        #         response = sse.send("Right Knee In!", tts_config=tts_config)
        #         player.play(response)
        #     #sse.play(tts_config, "Right Knee In!")


        cv2.imshow("Body recognition", image)
        if cv2.waitKey(10) & 0xFF == ord("q"):
            break

cap.release()
cv2.destroyAllWindows()