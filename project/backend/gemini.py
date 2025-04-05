from google import genai

client = genai.Client(api_key="AIzaSyDXCqquyDsiE97pAPc6uYzNml0sUN7_P4I")

response = client.models.generate_content(
    model="gemini-2.0-flash", contents="Explain the concept of gravity in simple terms."
)
print(response.text)