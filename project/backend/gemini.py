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

# Initialize Google GenAI client
genai_client = genai.Client(api_key=GEMINI_API_KEY)

# Initialize Neuphonic TTS client
neuphonic_client = Neuphonic(api_key=NEUPHONIC_API_KEY)
sse_client = neuphonic_client.tts.SSEClient()

# Memory to store conversation history
memory = ConversationBufferMemory(memory_key="chat_history")

# Function to capture audio and convert it to text using speech recognition
def capture_audio():
    recognizer = sr.Recognizer()
    mic = sr.Microphone()

    with mic as source:
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)

    try:
        # Convert speech to text
        text = recognizer.recognize_google(audio)
        print(f"You said: {text}")
        return text
    except sr.UnknownValueError:
        print("Sorry, I could not understand the audio.")
        return None
    except sr.RequestError as e:
        print(f"Could not request results from Google Speech Recognition service; {e}")
        return None

# Function to interact with Gemini API
def gemini_chat(input_text):
    try:

        # Get response from Gemini API
        response = genai_client.models.generate_content(
            model="gemini-2.0-flash",  # Specify model
            contents=input_text  # Pass user input
        )
        print(f"Gemini response: {response.text}")
        return response.text.strip()
    except Exception as e:
        print(f"Error in Gemini API call: {e}")
        return "Sorry, I couldn't get a response from Gemini. Please try again later."

# Function to generate TTS from Neuphonic
def generate_tts(response):
    tts_config = TTSConfig(
        lang_code='en',  # Set the language code
        sampling_rate=22050  # Set the audio sampling rate
    )

    try:
        with AudioPlayer(sampling_rate=22050) as player:
            # Generate the audio stream
            audio_stream = sse_client.send(response, tts_config=tts_config)
            player.play(audio_stream)
    except Exception as e:
        print(f"Error in speech synthesis: {e}")

# Create the conversation chain with memory
async def chat_with_gemini():
    print("🤖 Gemini chatbot is live! Say 'exit' to end the conversation.")

    while True:
        # Capture audio from the microphone
        user_input = capture_audio()

        if not user_input:
            continue

        # If user wants to exit the chat
        if user_input.lower() == 'exit':
            print("Goodbye! Chat session ended.")
            break

        # Add user input to memory
        memory.save_context({"input": user_input}, {"output": ""})

        # Get the response from the Gemini model
        conversation_context = memory.load_memory_variables({})['chat_history']
        response = gemini_chat(conversation_context + "\n" + user_input)

        # Save the response to memory
        memory.save_context({"input": user_input}, {"output": response})

        # Print Gemini's text response

        # Generate TTS using Neuphonic
        generate_tts(response)

# Run the chatbot
asyncio.run(chat_with_gemini())
