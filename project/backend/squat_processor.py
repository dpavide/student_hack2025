import cv2
import numpy as np
import mediapipe as mp
import time
from datetime import datetime
import json

# Modified logging setup
LOG_COOLDOWN = 0.1  # Increased from 0.05 to 0.5 seconds
last_log_times = {}  # Track cooldowns per feedback type

def log_feedback(message, coordinates):
    global last_log_times
    current_time = time.time()
    
    # Get last log time for this specific message
    last_time = last_log_times.get(message, 0)
    
    if current_time - last_time >= LOG_COOLDOWN:
        entry = {
            "timestamp": datetime.now().isoformat(),
            "feedback": message,
            "coordinates": coordinates
        }
        # Write to file immediately
        with open("temp.txt", "a") as f:
            f.write(json.dumps(entry) + "\n")
        
        # Update last log time for this message type
        last_log_times[message] = current_time

def process_squat(frame, results, mp_pose,
                  last_audio_time, audio_queue, perfect_form_flag, current_time,
                  AUDIO_COOLDOWN=3):
    feedback = "No pose detected"
    if results.pose_landmarks:
        landmarks = results.pose_landmarks.landmark

        def get_landmark_point(landmark, frame):
            return [landmark.x * frame.shape[1],
                    landmark.y * frame.shape[0],
                    landmark.z]

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

        # Get landmarks
        shoulderL = get_landmark_point(landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER], frame)
        shoulderR = get_landmark_point(landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER], frame)
        hipL = get_landmark_point(landmarks[mp_pose.PoseLandmark.LEFT_HIP], frame)
        hipR = get_landmark_point(landmarks[mp_pose.PoseLandmark.RIGHT_HIP], frame)
        kneeL = get_landmark_point(landmarks[mp_pose.PoseLandmark.LEFT_KNEE], frame)
        kneeR = get_landmark_point(landmarks[mp_pose.PoseLandmark.RIGHT_KNEE], frame)
        ankleL = get_landmark_point(landmarks[mp_pose.PoseLandmark.LEFT_ANKLE], frame)
        ankleR = get_landmark_point(landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE], frame)

        # Calculations
        angleKneeL = calculate_angle(hipL, kneeL, ankleL)
        angleKneeR = calculate_angle(hipR, kneeR, ankleR)
        midpointShoulder = calculate_midpoint(shoulderL, shoulderR)
        midpointHips = calculate_midpoint(hipL, hipR)
        midpointKnees = calculate_midpoint(kneeL, kneeR)
        angleBack = calculate_angle(midpointShoulder, midpointHips, midpointKnees)

        # Thresholds
        knee_valgus_threshold = 100
        back_lean_threshold = 65
        depth_threshold = 0.75
        depth_left = hipL[1] > kneeL[1] * depth_threshold
        depth_right = hipR[1] > kneeR[1] * depth_threshold
        current_depth_met = depth_left and depth_right
        knee_valgus_left = (kneeL[0] - ankleL[0]) > knee_valgus_threshold
        knee_valgus_right = (ankleR[0] - kneeR[0]) > knee_valgus_threshold

        perfect_form = False

        # Posture checks with logging
        if not current_depth_met:
            if (current_time - last_audio_time) > AUDIO_COOLDOWN:
                audio_queue.put("Go lower")
                last_audio_time = current_time
            feedback = "Go lower"
            perfect_form_flag = False
            log_feedback("go_lower", {
                "hips": [hipL, hipR],
                "knees": [kneeL, kneeR],
                "depth_met": current_depth_met
            })
        elif angleBack < back_lean_threshold:
            if (current_time - last_audio_time) > AUDIO_COOLDOWN:
                audio_queue.put("Lean forward too much")
                last_audio_time = current_time
            feedback = "Lean forward too much"
            log_feedback("lean_forward", {
                "body_angle": float(angleBack),
                "shoulder_mid": midpointShoulder,
                "hip_mid": midpointHips
            })
        elif knee_valgus_left:
            if (current_time - last_audio_time) > AUDIO_COOLDOWN:
                audio_queue.put("Left knee in")
                last_audio_time = current_time
            feedback = "Left knee in"
            log_feedback("knee_valgus_left", {
                "knee": kneeL,
                "ankle": ankleL
            })
        elif knee_valgus_right:
            if (current_time - last_audio_time) > AUDIO_COOLDOWN:
                audio_queue.put("Right knee in")
                last_audio_time = current_time
            feedback = "Right knee in"
            log_feedback("knee_valgus_right", {
                "knee": kneeR,
                "ankle": ankleR
            })
        else:
            perfect_form = True

        if perfect_form and current_depth_met:
            if not perfect_form_flag:
                audio_queue.put("Good form, go up")
                last_audio_time = current_time
                feedback = "Perfect! Go up!"
                perfect_form_flag = True
                log_feedback("perfect_form", {
                    "joint_angles": {
                        "knees": [float(angleKneeL), float(angleKneeR)],
                        "back": float(angleBack)
                    },
                    "depth_achieved": current_depth_met
                })
        else:
            perfect_form_flag = False

        # Visualization
        cv2.putText(frame, feedback, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(frame, f'{int(angleKneeL)}', (int(kneeL[0])-30, int(kneeL[1])-10), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, f'{int(angleKneeR)}', (int(kneeR[0])-30, int(kneeR[1])-10), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, f'{int(angleBack)}', (int(midpointHips[0])-30, int(midpointHips[1])-10), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        mp.solutions.drawing_utils.draw_landmarks(
            frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)

    return feedback, frame, perfect_form_flag, last_audio_time
