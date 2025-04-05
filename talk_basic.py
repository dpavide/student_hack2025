import os
from pyneuphonic import Neuphonic, TTSConfig
from pyneuphonic.player import AudioPlayer

# Ensure the API key is set in your environment
client = Neuphonic(api_key=os.environ.get('NEUPHONIC_API_KEY'))

sse = client.tts.SSEClient()

# TTSConfig is a pydantic model so check out the source code for all valid options
tts_config = TTSConfig(
    lang_code='en', # replace the lang_code with the desired language code.
    sampling_rate=22050,
)

# Create an audio player with `pyaudio`
# Make sure you use the same sampling rate as in the TTSConfig
with AudioPlayer(sampling_rate=22050) as player:
    response = sse.send('Hello, world!', tts_config=tts_config)
    player.play(response)