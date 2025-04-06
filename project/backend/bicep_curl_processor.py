import cv2
import numpy as np
import mediapipe as mp
from datetime import datetime
import json
import time

def log_feedback(feedback_type, coordinates):
    entry = {
        "timestamp": datetime.now().isoformat(),
        "feedback": feedback_type,
        "coordinates": coordinates
    }
    with open("bicep_log.txt", "a") as f:
        f.write(json.dumps(entry) + "\n")

def calculate_angle(a, b, c):
    a = np.array(a[:2])
    b = np.array(b[:2])
    c = np.array(c[:2])
    
    radians = np.arctan2(c[1]-b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
    angle = np.abs(np.degrees(radians))
    
    return angle if angle <= 180 else 360 - angle

def get_landmark_point(landmark, frame_shape):
    return [landmark.x * frame_shape[1],
            landmark.y * frame_shape[0],
            landmark.z]

def process_bicep_curl(frame, results, mp_pose, last_audio_time, audio_queue, bicep_phase, current_time, AUDIO_COOLDOWN):
    feedback = "No pose detected"
    frame_shape = frame.shape
    annotated_frame = frame.copy()
    perfect_form_flag = False

    if results.pose_landmarks:
        landmarks = results.pose_landmarks.landmark

        # Get landmarks
        shoulderL = get_landmark_point(landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER], frame_shape)
        elbowL = get_landmark_point(landmarks[mp_pose.PoseLandmark.LEFT_ELBOW], frame_shape)
        wristL = get_landmark_point(landmarks[mp_pose.PoseLandmark.LEFT_WRIST], frame_shape)
        hipL = get_landmark_point(landmarks[mp_pose.PoseLandmark.LEFT_HIP], frame_shape)

        # Calculate angles
        elbow_angle = int(calculate_angle(shoulderL, elbowL, wristL))
        back_lean = abs(shoulderL[0] - hipL[0]) / frame_shape[1] * 100  # Percentage

        # Bicep curl logic
        feedback_given = False
        ELBOW_RANGE = {'down': 170, 'up': 30}
        BACK_LEAN_THRESHOLD = 10  # Changed from 15 to 10 (more sensitive)
        
        if elbow_angle > ELBOW_RANGE['down']:
            bicep_phase = "down"
        elif elbow_angle < ELBOW_RANGE['up'] and bicep_phase == "down":
            bicep_phase = "up"
            audio_queue.put(f"Rep counted")
            log_feedback("rep_completed", {
                "elbow_angle": elbow_angle,
                "joints": {
                    "shoulder": shoulderL,
                    "elbow": elbowL,
                    "wrist": wristL
                }
            })

        # Feedback conditions
        if bicep_phase == "up" and elbow_angle > ELBOW_RANGE['up'] + 20:
            if (current_time - last_audio_time) > AUDIO_COOLDOWN:
                audio_queue.put("Lift higher")
                last_audio_time = current_time
                log_feedback("lift_higher", {
                    "elbow_angle": elbow_angle,
                    "elbow_position": elbowL,
                    "wrist_position": wristL
                })
                feedback = "Lift Higher!"
                feedback_given = True

        if back_lean > BACK_LEAN_THRESHOLD:  # Updated threshold
            if (current_time - last_audio_time) > AUDIO_COOLDOWN and not feedback_given:
                audio_queue.put("Keep your back straight")
                last_audio_time = current_time
                log_feedback("back_lean", {
                    "shoulder_hip_diff": back_lean,
                    "shoulder_position": shoulderL,
                    "hip_position": hipL
                })
                feedback = "Keep Back Straight!"
                feedback_given = True

        if not feedback_given and bicep_phase == "up" and elbow_angle <= ELBOW_RANGE['up'] + 20:
            feedback = "Good form!"
            log_feedback("good_form", {
                "elbow_angle": elbow_angle,
                "back_lean": back_lean
            })

        # Visualization
        cv2.putText(annotated_frame, feedback, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(annotated_frame, f'Elbow: {elbow_angle}°', (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(annotated_frame, f'Back Lean: {int(back_lean)}%', (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
        mp.solutions.drawing_utils.draw_landmarks(
            annotated_frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)

    return feedback, annotated_frame, bicep_phase, last_audio_time