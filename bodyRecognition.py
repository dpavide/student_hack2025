import mediapipe as mp
import cv2

# Set up for mediapipe
mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose

cap = cv2.VideoCapture(0)
# --- Main loop for openCV ---
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
