import cv2
import numpy as np

def process_squat(frame, results, mp_pose, mp_drawing,
                  last_audio_time, audio_queue, perfect_form_flag, current_time,
                  AUDIO_COOLDOWN=3):
    """
    Process the frame for squat analysis.
    Returns:
      feedback (str), annotated frame, updated perfect_form_flag, updated last_audio_time.
    """
    feedback = "No pose detected"
    if results.pose_landmarks:
        landmarks = results.pose_landmarks.landmark

        def get_landmark_point(landmark, frame):
            return [int(landmark.x * frame.shape[1]),
                    int(landmark.y * frame.shape[0]),
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
            return [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2, (a[2] + b[2]) / 2]

        # Get key landmarks
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

        perfect_form = False

        # Check conditions and trigger audio cues if needed
        if not current_depth_met:
            if (current_time - last_audio_time) > AUDIO_COOLDOWN:
                audio_queue.put("Go lower")
                last_audio_time = current_time
            feedback = "Go lower"
            perfect_form_flag = False
        elif angleBack < back_lean_threshold:
            if (current_time - last_audio_time) > AUDIO_COOLDOWN:
                audio_queue.put("Lean forward too much")
                last_audio_time = current_time
            feedback = "Lean forward too much"
        elif knee_valgus_left:
            if (current_time - last_audio_time) > AUDIO_COOLDOWN:
                audio_queue.put("Left knee in")
                last_audio_time = current_time
            feedback = "Left knee in"
        elif knee_valgus_right:
            if (current_time - last_audio_time) > AUDIO_COOLDOWN:
                audio_queue.put("Right knee in")
                last_audio_time = current_time
            feedback = "Right knee in"
        else:
            perfect_form = True

        if perfect_form:
            if current_depth_met:
                if not perfect_form_flag:
                    if (current_time - last_audio_time) > AUDIO_COOLDOWN:
                        audio_queue.put("Good form, go up")
                        last_audio_time = current_time
                    feedback = "Perfect! Go up!"
                    perfect_form_flag = True
            else:
                perfect_form_flag = False

        # Draw text and landmarks on frame
        cv2.putText(frame, feedback, (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(frame, f'{angleKneeL}', (int(kneeL[0] - 30), int(kneeL[1] - 10)),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(frame, f'{angleKneeR}', (int(kneeR[0] - 30), int(kneeR[1] - 10)),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(frame, f'{int(angleBack)}', (int(midpointHips[0] - 30), int(midpointHips[1] - 10)),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        mp_drawing.draw_landmarks(frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
        feedback = "Analysis complete"
    return feedback, frame, perfect_form_flag, last_audio_time
