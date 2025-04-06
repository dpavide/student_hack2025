import cv2
import numpy as np
import mediapipe as mp
from datetime import datetime
import json
from mediapipe.python.solutions.pose import PoseLandmark

def calculate_angle(a, b, c):
    a2d = np.array(a[:2])
    b2d = np.array(b[:2])
    c2d = np.array(c[:2])
    ba = a2d - b2d
    bc = c2d - b2d
    cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
    angle = np.arccos(np.clip(cosine_angle, -1.0, 1.0))
    return np.degrees(angle)

def get_landmark_point(landmark, frame_shape):
    return [landmark.x * frame_shape[1],
            landmark.y * frame_shape[0],
            landmark.z]

def log_feedback(feedback_type, coordinates):
    entry = {
        "timestamp": datetime.now().isoformat(),
        "feedback": feedback_type,
        "coordinates": coordinates
    }
    with open("pushup_log.txt", "a") as f:
        f.write(json.dumps(entry) + "\n")

def process_pushup(frame, results, mp_pose, last_audio_time, audio_queue, pushup_phase, current_time, AUDIO_COOLDOWN):
    feedback = "No pushup detected"
    frame_shape = frame.shape
    annotated_frame = frame.copy()

    try:
        if results.pose_landmarks:
            landmarks = results.pose_landmarks.landmark

            # Get key landmarks
            shoulderL = get_landmark_point(landmarks[PoseLandmark.LEFT_SHOULDER], frame_shape)
            shoulderR = get_landmark_point(landmarks[PoseLandmark.RIGHT_SHOULDER], frame_shape)
            elbowL = get_landmark_point(landmarks[PoseLandmark.LEFT_ELBOW], frame_shape)
            elbowR = get_landmark_point(landmarks[PoseLandmark.RIGHT_ELBOW], frame_shape)
            wristL = get_landmark_point(landmarks[PoseLandmark.LEFT_WRIST], frame_shape)
            wristR = get_landmark_point(landmarks[PoseLandmark.RIGHT_WRIST], frame_shape)
            hipL = get_landmark_point(landmarks[PoseLandmark.LEFT_HIP], frame_shape)
            hipR = get_landmark_point(landmarks[PoseLandmark.RIGHT_HIP], frame_shape)
            kneeL = get_landmark_point(landmarks[PoseLandmark.LEFT_KNEE], frame_shape)

            # Calculate angles
            angleElbowL = int(calculate_angle(shoulderL, elbowL, wristL))
            angleElbowR = int(calculate_angle(shoulderR, elbowR, wristR))
            angleShoulderL = int(calculate_angle(hipL, shoulderL, elbowL))
            angleShoulderR = int(calculate_angle(hipR, shoulderR, elbowR))
            raw_spine_angle = calculate_angle(shoulderL, hipL, kneeL)
            spine_angle = int(raw_spine_angle) if not np.isnan(raw_spine_angle) else 0

            # Feedback conditions thresholds (you can adjust these values)
            if angleShoulderL > 100 or angleShoulderR > 100:
                msg = "Shoulders too wide"
                feedback_type = "shoulders_too_wide"
                coordinates = {
                    "shoulders": [shoulderL, shoulderR],
                    "elbows": [elbowL, elbowR]
                }
                if (current_time - last_audio_time) > AUDIO_COOLDOWN:
                    audio_queue.put(msg)
                    last_audio_time = current_time
                log_feedback(feedback_type, coordinates)
                feedback = msg

            elif angleShoulderL < 10 or angleShoulderR < 10:
                msg = "Shoulders too narrow"
                feedback_type = "shoulders_too_narrow"
                coordinates = {
                    "shoulders": [shoulderL, shoulderR],
                    "elbows": [elbowL, elbowR]
                }
                if (current_time - last_audio_time) > AUDIO_COOLDOWN:
                    audio_queue.put(msg)
                    last_audio_time = current_time
                log_feedback(feedback_type, coordinates)
                feedback = msg

            elif spine_angle < 155:
                msg = "Keep your back straight"
                feedback_type = "back_not_straight"
                coordinates = {
                    "shoulders": [shoulderL, shoulderR],
                    "hips": [hipL, hipR],
                    "spine_angle": spine_angle
                }
                if (current_time - last_audio_time) > AUDIO_COOLDOWN:
                    audio_queue.put(msg)
                    last_audio_time = current_time
                log_feedback(feedback_type, coordinates)
                feedback = msg

            # Conditions for pushup phase transitions
            elif pushup_phase == "down" and (angleElbowL > 95 or angleElbowR > 95):
                msg = "Go deeper"
                feedback_type = "go_deeper"
                coordinates = {
                    "elbows": [elbowL, elbowR],
                    "shoulders": [shoulderL, shoulderR],
                    "depth_met": False
                }
                if (current_time - last_audio_time) > AUDIO_COOLDOWN:
                    audio_queue.put(msg)
                    last_audio_time = current_time
                log_feedback(feedback_type, coordinates)
                feedback = msg

            elif pushup_phase == "up" and (angleElbowL < 90 or angleElbowR < 90):
                msg = "Control your ascent"
                feedback_type = "ascent_control"
                coordinates = {
                    "elbows": [elbowL, elbowR],
                    "shoulders": [shoulderL, shoulderR]
                }
                if (current_time - last_audio_time) > AUDIO_COOLDOWN:
                    audio_queue.put(msg)
                    last_audio_time = current_time
                log_feedback(feedback_type, coordinates)
                feedback = msg

            # Good form transition
            if feedback == "No pushup detected" or feedback == "":
                if pushup_phase == "down" and angleElbowL < 95 and angleElbowR < 95 and spine_angle >= 155:
                    audio_queue.put("Good form, push up")
                    feedback = "Perfect! Push Up!"
                    log_feedback("perfect_form", {
                        "joint_angles": {
                            "elbows": [angleElbowL, angleElbowR],
                            "shoulders": [angleShoulderL, angleShoulderR]
                        },
                        "spine": spine_angle
                    })
                    pushup_phase = "up"
                elif pushup_phase == "up" and angleElbowL > 90 and angleElbowR > 90 and spine_angle >= 155:
                    audio_queue.put("Good form, lower down")
                    feedback = "Good! Lower Down!"
                    log_feedback("perfect_form", {
                        "joint_angles": {
                            "elbows": [angleElbowL, angleElbowR],
                            "shoulders": [angleShoulderL, angleShoulderR]
                        },
                        "spine": spine_angle
                    })
                    pushup_phase = "down"

            # Draw annotations on frame
            cv2.putText(annotated_frame, feedback, (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.putText(annotated_frame, f'{angleElbowL}', (int(elbowL[0]) - 30, int(elbowL[1]) - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(annotated_frame, f'{angleElbowR}', (int(elbowR[0]) - 30, int(elbowR[1]) - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(annotated_frame, f'{spine_angle}', (int(hipL[0]) - 30, int(hipL[1]) - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            mp.solutions.drawing_utils.draw_landmarks(
                annotated_frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
            
            print("complete")

    except Exception as e:
        print(f"Pushup processing error: {e}")

    return feedback, annotated_frame, pushup_phase, last_audio_time
