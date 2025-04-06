import cv2
import numpy as np
import mediapipe as mp
from datetime import datetime
import json
import random
from mediapipe.python.solutions.pose import PoseLandmark

def calculate_angle(a, b, c):
    """Calculate angle between three points with safety checks"""
    if None in [a, b, c] or len(a) < 2 or len(b) < 2 or len(c) < 2:
        return None

    a2d = np.array(a[:2])
    b2d = np.array(b[:2])
    c2d = np.array(c[:2])

    ba = a2d - b2d
    bc = c2d - b2d

    if np.linalg.norm(ba) == 0 or np.linalg.norm(bc) == 0:
        return None

    cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
    angle = np.degrees(np.arccos(np.clip(cosine_angle, -1.0, 1.0)))
    return angle

def get_landmark_point(landmark, frame_shape, visibility_threshold=0.3):
    """Get landmark coordinates with adjustable visibility threshold"""
    if landmark.visibility < visibility_threshold:
        return None
    return [
        landmark.x * frame_shape[1],
        landmark.y * frame_shape[0],
        landmark.z
    ]

def log_feedback(feedback_type, coordinates):
    entry = {
        "timestamp": datetime.now().isoformat(),
        "feedback": feedback_type,
        "coordinates": coordinates
    }
    with open("pushup_log.txt", "a") as f:
        f.write(json.dumps(entry) + "\n")

ENCOURAGEMENT = {
    'perfect_down': ["Awesome depth!", "Great range!", "Perfect form!", "Excellent going down!"],
    'perfect_up': ["Strong push!", "Great extension!", "Nice control!", "Powerful ascent!"],
    'partial_rep': ["You've got this!", "Keep going!", "One more rep!", "Almost there!"],
    'form_reminder': ["Core tight!", "Body straight!", "You're doing great!", "Maintain form!"],
    'general': ["Every rep counts!", "You're getting stronger!", "Consistency is key!", "Progress happens daily!"]
}

def get_encouragement(key):
    return random.choice(ENCOURAGEMENT[key])

def process_pushup(frame, results, mp_pose, last_audio_time, audio_queue, pushup_phase, current_time, AUDIO_COOLDOWN):
    feedback = random.choice(ENCOURAGEMENT['general']) + " Let's go!"
    frame_shape = frame.shape
    annotated_frame = frame.copy()

    # Modified thresholds
    ELBOW_DOWN_THRESHOLD = 110
    ELBOW_UP_THRESHOLD = 160
    SPINE_ANGLE_MAX = 180
    SPINE_ANGLE_MIN = 60

    try:
        if results.pose_landmarks:
            landmarks = results.pose_landmarks.landmark

            # Get key landmarks
            landmark_points = {
                'shoulderL': get_landmark_point(landmarks[PoseLandmark.LEFT_SHOULDER], frame_shape, 0.3),
                'shoulderR': get_landmark_point(landmarks[PoseLandmark.RIGHT_SHOULDER], frame_shape, 0.3),
                'elbowL': get_landmark_point(landmarks[PoseLandmark.LEFT_ELBOW], frame_shape, 0.3),
                'elbowR': get_landmark_point(landmarks[PoseLandmark.RIGHT_ELBOW], frame_shape, 0.3),
                'wristL': get_landmark_point(landmarks[PoseLandmark.LEFT_WRIST], frame_shape, 0.3),
                'wristR': get_landmark_point(landmarks[PoseLandmark.RIGHT_WRIST], frame_shape, 0.3),
                'hipL': get_landmark_point(landmarks[PoseLandmark.LEFT_HIP], frame_shape, 0.3),
                'hipR': get_landmark_point(landmarks[PoseLandmark.RIGHT_HIP], frame_shape, 0.3),
                'kneeL': get_landmark_point(landmarks[PoseLandmark.LEFT_KNEE], frame_shape, 0.1),
            }

            critical_points = ['shoulderL', 'shoulderR', 'elbowL', 'elbowR', 'hipL', 'hipR']
            if any(landmark_points[p] is None for p in critical_points):
                return feedback, annotated_frame, pushup_phase, last_audio_time

            angleElbowL = calculate_angle(landmark_points['shoulderL'], landmark_points['elbowL'], landmark_points['wristL'])
            angleElbowR = calculate_angle(landmark_points['shoulderR'], landmark_points['elbowR'], landmark_points['wristR'])
            angleShoulderL = calculate_angle(landmark_points['hipL'], landmark_points['shoulderL'], landmark_points['elbowL'])
            angleShoulderR = calculate_angle(landmark_points['hipR'], landmark_points['shoulderR'], landmark_points['elbowR'])

            spine_angle = None
            if landmark_points['kneeL'] is not None:
                raw_spine_angle = calculate_angle(landmark_points['shoulderL'], landmark_points['hipL'], landmark_points['kneeL'])
                spine_angle = int(raw_spine_angle) if raw_spine_angle is not None else None

            if any(a is None for a in [angleElbowL, angleElbowR, angleShoulderL, angleShoulderR]):
                return feedback, annotated_frame, pushup_phase, last_audio_time

            def should_play_audio(msg):
                return (current_time - last_audio_time) > AUDIO_COOLDOWN and (audio_queue.empty() or audio_queue.queue[-1] != msg)

            # Phase detection with encouragement
            if pushup_phase == "down" and angleElbowL < ELBOW_DOWN_THRESHOLD and angleElbowR < ELBOW_DOWN_THRESHOLD:
                msg = f"{get_encouragement('perfect_down')} Perfect, push up now!"
                feedback = f"Perfect! Push up! ({(180 - int(max(angleElbowL, angleElbowR)))}° depth)"
                log_feedback("good_form", {
                    "joint_angles": {
                        "elbows": [angleElbowL, angleElbowR],
                        "shoulders": [angleShoulderL, angleShoulderR]
                    },
                    "spine": spine_angle
                })
                pushup_phase = "up"
                if should_play_audio(msg):
                    audio_queue.put(msg)
                    last_audio_time = current_time

            elif pushup_phase == "up" and angleElbowL > ELBOW_UP_THRESHOLD and angleElbowR > ELBOW_UP_THRESHOLD:
                msg = f"{get_encouragement('perfect_up')} Try lower down!"
                feedback = f"Great! Lower down! ({int(min(angleElbowL, angleElbowR))}° extension)"
                log_feedback("good_form", {
                    "joint_angles": {
                        "elbows": [angleElbowL, angleElbowR],
                        "shoulders": [angleShoulderL, angleShoulderR]
                    },
                    "spine": spine_angle
                })
                pushup_phase = "down"
                if should_play_audio(msg):
                    audio_queue.put(msg)
                    last_audio_time = current_time

            # Form feedback with positive reinforcement
            elif spine_angle is not None:
                if spine_angle > SPINE_ANGLE_MAX:
                    msg = f"{get_encouragement('form_reminder')} Straighten your back!"
                    feedback = "Almost perfect! Straighten your back a bit"
                    log_feedback("form_reminder", {"spine_angle": spine_angle})
                elif spine_angle < SPINE_ANGLE_MIN:
                    msg = f"{get_encouragement('form_reminder')} Hips down!"
                    feedback = " Keep hips down for better form!"
                    log_feedback("form_reminder", {"spine_angle": spine_angle})
                
                if should_play_audio(msg):
                    audio_queue.put(msg)
                    last_audio_time = current_time

            elif pushup_phase == "down" and (angleElbowL > ELBOW_DOWN_THRESHOLD or angleElbowR > ELBOW_DOWN_THRESHOLD):
                msg = f"Keep going lower"
                feedback = f"Almost there! Current: {int(max(angleElbowL, angleElbowR))}°"
                log_feedback("depth_reminder", {"elbow_angles": [angleElbowL, angleElbowR]})
                if should_play_audio(msg):
                    audio_queue.put(msg)
                    last_audio_time = current_time

            elif pushup_phase == "up" and (angleElbowL < ELBOW_UP_THRESHOLD or angleElbowR < ELBOW_UP_THRESHOLD):
                msg = f"{get_encouragement('partial_rep')} Push to full extension!"
                feedback = f" Keep pushing! Current: {int(min(angleElbowL, angleElbowR))}°"
                log_feedback("ascent_reminder", {"elbow_angles": [angleElbowL, angleElbowR]})
                if should_play_audio(msg):
                    audio_queue.put(msg)
                    last_audio_time = current_time

            # Random encouragement
            if random.random() < 0.4:  # 40% chance of extra encouragement
                encouragement = random.choice([
                    "You're crushing it!",
                    "Strong work!",
                    "That's the spirit!",
                    "Progress feels good!"
                ])
                feedback += f" {encouragement}"

            # Visualization
            cv2.putText(annotated_frame, feedback, (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 100), 2)
            
            # Add motivational elements
            if pushup_phase == "up":
                cv2.putText(annotated_frame, "↑ PUSH STRONG ↑", (frame_shape[1]-300, 50),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (100, 255, 100), 2)
            else:
                cv2.putText(annotated_frame, "↓ CONTROL DESCENT ↓", (frame_shape[1]-350, 50),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (100, 255, 100), 2)

            # Angle displays
            if landmark_points['elbowL']:
                cv2.putText(annotated_frame, f'L: {int(angleElbowL)}°', 
                            (int(landmark_points['elbowL'][0])-30, int(landmark_points['elbowL'][1])-10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 200, 200), 2)
            if landmark_points['elbowR']:
                cv2.putText(annotated_frame, f'R: {int(angleElbowR)}°', 
                            (int(landmark_points['elbowR'][0])-30, int(landmark_points['elbowR'][1])-10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 200, 200), 2)

            mp.solutions.drawing_utils.draw_landmarks(
                annotated_frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS,
                landmark_drawing_spec=mp.solutions.drawing_styles.get_default_pose_landmarks_style())

    except Exception as e:
        print(f"Pushup processing error: {e}")

    return feedback, annotated_frame, pushup_phase, last_audio_time