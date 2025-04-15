# 🏋️‍♂️ Gym Bro

A real-time fitness feedback app that uses your webcam to analyze form and provide instant coaching — built with **Flask**, **OpenCV**, **MediaPipe**, and **GenAI**. Built in under 24 hours at [StudentHack 2025](https://studenthack.com), where it placed Top 3.

![Demo](./demo.gif)

---

## ⚡ Live Demo

🚧 [Coming Soon] — currently under active development

---

## 🧠 About

Gym Bro helps users improve their workout form by providing instant posture feedback through computer vision. We used **MediaPipe Pose Detection** to track body landmarks and generate insights using **GenAI-powered voice coaching**.

This project was built in 24 hours by a team of 4. I led real-time vision integration, backend infrastructure, and deployed a working prototype during the hackathon.

---

## ⚙️ Tech Stack

| Layer        | Stack                                         |
|--------------|-----------------------------------------------|
| Frontend     | React Native, Expo, Axios                     |
| Backend      | Flask, MediaPipe, OpenCV, GenAI API, Neuphonic |
| Deployment   | Localhost / Expo Go for mobile preview        |

---

## 🚀 Features

- 🧍 Pose detection using MediaPipe + OpenCV  
- 🧠 Real-time analysis of body movement  
- 🔈 Voice feedback via Google GenAI + Neuphonic API  
- 📱 Mobile-friendly interface (React Native + Expo)  
- 💬 JSON-based backend communication with Flask API  

---

## 🖥 Run Locally

```bash
# Backend
cd backend
pip install -r requirements.txt
python app.py

# Frontend
cd frontend
npm install
npx expo start
