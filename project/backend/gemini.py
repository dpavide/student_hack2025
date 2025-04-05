import os
import speech_recognition as sr
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

SYSTEM_PROMPT = ""

# Initialize Google GenAI client
genai_client = genai.Client(api_key=GEMINI_API_KEY)

# Initialize Neuphonic TTS client
neuphonic_client = Neuphonic(api_key=NEUPHONIC_API_KEY)
sse_client = neuphonic_client.tts.SSEClient()

# Memory to store conversation history
memory = ConversationBufferMemory(memory_key="chat_history")

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
        # Get conversation history
        conversation_history = memory.load_memory_variables({})['chat_history']
        
        # Build full prompt with system instruction
        full_prompt = f"{SYSTEM_PROMPT}\n\n{conversation_history}\nUser: {user_input}"
        
        # Send to Gemini
        response = genai_client.models.generate_content(
            model="gemini-2.0-flash",
            contents=full_prompt
        )
        print(f"Gemini response: {response.text}")
        return response.text.strip()
    except Exception as e:
        print(f"Error in Gemini API call: {e}")
        return "Sorry, I couldn't get a response. Please try again."

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
    
    # Initialize with system prompt
    memory.save_context({"input": "System"}, {"output": SYSTEM_PROMPT})

    while True:
        user_input = capture_audio()

        if not user_input:
            continue

        if user_input.lower() == 'exit':
            print("Goodbye! Chat session ended.")
            break

        # Get response
        response = gemini_chat(user_input)

        # Save conversation
        memory.save_context({"input": user_input}, {"output": response})

        # Generate TTS
        generate_tts(response)

asyncio.run(chat_with_gemini())