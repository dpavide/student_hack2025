import numpy as np
import mediapipe as mp
from PIL import Image
import io
import base64
import os

# Set up MediaPipe Pose
mp_pose = mp.solutions.pose

def calculate_angle(a, b, c):
    a2d = np.array(a[:2])
    b2d = np.array(b[:2])
    c2d = np.array(c[:2])
    ba = a2d - b2d
    bc = c2d - b2d
    cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
    angle = np.arccos(np.clip(cosine_angle, -1.0, 1.0))
    return np.degrees(angle)

def analyze_body_pose(pil_image: Image.Image) -> str:
    """
    Process a PIL image using MediaPipe in static image mode
    and return feedback based on the detected pose.
    """
    # Convert PIL image to numpy array in RGB
    image_array = np.array(pil_image.convert('RGB'))
    h, w, _ = image_array.shape

    # Initialize MediaPipe Pose in static image mode
    with mp_pose.Pose(static_image_mode=True, min_detection_confidence=0.6) as pose:
        results = pose.process(image_array)

        # Check if landmarks are detected
        if not results.pose_landmarks:
            return "No pose detected. Please try again."

        landmarks = results.pose_landmarks.landmark

        # Helper to convert normalized landmarks to pixel coordinates
        def get_landmark_point(landmark):
            return [int(landmark.x * w), int(landmark.y * h), landmark.z]

        # Example: Calculate left elbow angle
        shoulderL = get_landmark_point(landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value])
        elbowL    = get_landmark_point(landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value])
        wristL    = get_landmark_point(landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value])
        angleElbowL = calculate_angle(shoulderL, elbowL, wristL)

        # (You can add similar calculations for other body parts.)
        # For demonstration, let’s provide basic feedback based on the left elbow angle.
        if angleElbowL < 40:
            feedback = "Your left elbow angle is too small. Try to relax your arm."
        else:
            feedback = "Good form detected!"

        return feedback
