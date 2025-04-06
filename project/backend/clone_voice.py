import os
from pyneuphonic import Neuphonic

# Ensure the API key is set in your environment
client = Neuphonic(api_key="8fb2c4088c78679a39ebaf3880453fee56a16baca7956a92af618a5222a8119f.d981e780-3140-4206-848d-d323f3d0b79c")

response = client.voices.clone(
    voice_name='satvik',
    voice_file_path='project/voices/will_smith.mp3'  # replace with file path to a sample of the voice to clone
)

print(response.data)  # this will contain a success message with the voice_id of the cloned voice
voice_id = response.data['voice_id']  # store the voice_id for later use