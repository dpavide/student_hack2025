import mediapipe as mp
import cv2
import numpy as np

# Set up for mediapipe
mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose

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
    return (a+b)/2

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

        except Exception as e:
            if e == "'NoneType' object has no attribute 'landmark'":
                pass
            else:
                print("Error processing pose:", e)
        
        mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)

        cv2.imshow("Body recognition", image)
        if cv2.waitKey(10) & 0xFF == ord("q"):
            break

cap.release()
cv2.destroyAllWindows()