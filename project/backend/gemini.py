import os
import speech_recognition as sr
import json
from google import genai
from dotenv import load_dotenv
import asyncio
from pyneuphonic import Neuphonic, TTSConfig
from pyneuphonic.player import AudioPlayer
from langchain.memory import ConversationBufferMemory

# Load environment variables
load_dotenv()

# Retrieve API keys from environment
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
NEUPHONIC_API_KEY = os.environ.get("NEUPHONIC_API_KEY")

SYSTEM_PROMPT = """You are an expert fitness coach analyzing squat form data. The data is provided with timestamps so that if the user does something wrong, you have multiple landmarks to work with. The perfect form landmarks have more weight since they're only added once to the text each time compared to the multiple time stamps of the incorrect form. Make use of the coordinates in your analysis. Your task is to:
1. Output should be summarised to reduce how long the message is. Only include key, necessary points.
2. Identify patterns in the form feedback data
3. Highlight 2-3 key areas for improvement
4. Recognize what the user did well
5. Provide specific, actionable advice
6. Maintain an encouraging, positive tone
7. Be prepared to answer follow-up questions about the analysis
8. Make sure the analysis isn't too long. Try keeping it to around 100 words. It should be 30-45 seconds to read out-loud. However, if you're asked for timestamps, allow for longer text output"""

# Initialize Google GenAI client
genai_client = genai.Client(api_key=GEMINI_API_KEY)

# Initialize Neuphonic TTS client
neuphonic_client = Neuphonic(api_key=NEUPHONIC_API_KEY)
sse_client = neuphonic_client.tts.SSEClient()

# Memory to store conversation history
memory = ConversationBufferMemory(memory_key="chat_history")

def load_squat_data():
    """Load and parse the feedback log file"""
    entries = []
    try:
        with open("temp.txt", "r") as f:
            for line in f:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        return entries
    except FileNotFoundError:
        return []

def capture_audio():
    recognizer = sr.Recognizer()
    mic = sr.Microphone()

    with mic as source:
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)

    try:
        text = recognizer.recognize_google(audio)
        print(f"You said: {text}")
        return text
    except sr.UnknownValueError:
        print("Sorry, I could not understand the audio.")
        return None
    except sr.RequestError as e:
        print(f"Could not request results from Google Speech Recognition service; {e}")
        return None

def gemini_chat(user_input):
    try:
        conversation_history = memory.load_memory_variables({})['chat_history']
        
        full_prompt = f"{SYSTEM_PROMPT}\n\n{conversation_history}\nUser: {user_input}"
        
        response = genai_client.models.generate_content(
            model="gemini-2.0-flash",
            contents=full_prompt
        )
        print(f"Gemini response: {response.text}")
        return response.text.strip()
    except Exception as e:
        print(f"Error in Gemini API call: {e}")
        return "Sorry, I couldn't process that. Please try again."

def generate_tts(response):
    tts_config = TTSConfig(
        lang_code='en',
        sampling_rate=22050
    )

    try:
        with AudioPlayer(sampling_rate=22050) as player:
            audio_stream = sse_client.send(response, tts_config=tts_config)
            player.play(audio_stream)
    except Exception as e:
        print(f"Error in speech synthesis: {e}")

async def chat_with_gemini():
    print("🤖 Gemini chatbot is live! Say 'exit' to end the conversation.")
    
    # Initialize system prompt
    memory.save_context({"input": "System"}, {"output": SYSTEM_PROMPT})

    # Automatic squat analysis on startup
    squat_data = load_squat_data()
    if squat_data:
        analysis_request = f"Analyze this squat form data: {json.dumps(squat_data)}. Provide detailed feedback and be ready for questions."
        analysis_response = gemini_chat(analysis_request)
        memory.save_context({"input": analysis_request}, {"output": analysis_response})
        generate_tts(analysis_response)
    else:
        generate_tts("No squat data found. Complete a workout session first!")

    # Conversation loop
    while True:
        user_input = capture_audio()

        if not user_input:
            continue

        if user_input.lower() == 'exit':
            print("Goodbye! Chat session ended.")
            break

        response = gemini_chat(user_input)
        memory.save_context({"input": user_input}, {"output": response})
        generate_tts(response)

asyncio.run(chat_with_gemini())
